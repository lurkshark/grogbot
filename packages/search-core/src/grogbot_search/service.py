from __future__ import annotations

import html
import re
import pysqlite3 as sqlite3
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional
from urllib.parse import urlparse

import httpx
from dateutil import parser as date_parser
from markdownify import markdownify as html_to_markdown
from readability import Document as ReadabilityDocument
from bs4 import BeautifulSoup

from grogbot_search.chunking import chunk_markdown
from grogbot_search.embeddings import embed_texts
from grogbot_search.ids import document_id_for_url, source_id_for_domain
from grogbot_search.models import Chunk, Document, SearchResult, Source


@dataclass
class SearchScores:
    fts: float
    vector: float
    hybrid: float


def _normalize_domain(url: str) -> str:
    return urlparse(url).netloc.lower()


def _canonicalize_url(url: str) -> str:
    return url.strip()


def _extract_feed_urls_from_opml(xml_content: str) -> List[str]:
    """Parse OPML XML and extract all xmlUrl values from nested outline elements."""
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as exc:
        raise ValueError(f"Invalid OPML XML: {exc}") from exc

    urls: List[str] = []

    def _extract_outlines(element):
        for outline in element.findall(".//outline"):
            xml_url = outline.get("xmlUrl")
            if xml_url:
                urls.append(xml_url.strip())

    _extract_outlines(root)
    return urls


def _local_tag_name(tag: str) -> str:
    """Return XML tag name without namespace."""
    return tag.split("}", 1)[-1] if "}" in tag else tag


def _extract_urls_from_sitemap(xml_content: str) -> List[str]:
    """Parse sitemap XML and extract all <url><loc> values."""
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as exc:
        raise ValueError(f"Invalid sitemap XML: {exc}") from exc

    urls: List[str] = []
    for element in root.iter():
        if _local_tag_name(element.tag) != "url":
            continue
        for child in element:
            if _local_tag_name(child.tag) == "loc" and child.text:
                urls.append(child.text.strip())
                break
    return urls


def _dedupe_urls(urls: Iterable[str]) -> List[str]:
    """Deduplicate URLs while preserving order."""
    seen: set[str] = set()
    unique_urls: List[str] = []
    for url in urls:
        normalized = _canonicalize_url(url)
        if normalized not in seen:
            seen.add(normalized)
            unique_urls.append(normalized)
    return unique_urls


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return date_parser.parse(value)
    except (ValueError, TypeError):
        return None


def _serialize_datetime(value: Optional[datetime]) -> Optional[str]:
    return value.isoformat() if value else None


def _extract_canonical_url(html: str, fallback: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    link = soup.find("link", rel="canonical")
    href = link.get("href") if link else None
    return _canonicalize_url(href or fallback)


def _extract_meta_content(html: str, name: str, attr: str = "name") -> Optional[str]:
    soup = BeautifulSoup(html, "html.parser")
    tag = soup.find("meta", attrs={attr: name})
    return tag.get("content") if tag else None


def _extract_published_at(html: str) -> Optional[datetime]:
    for attr, value in [("property", "article:published_time"), ("name", "pubdate")]:
        meta = _extract_meta_content(html, value, attr=attr)
        if meta:
            parsed = _parse_datetime(meta)
            if parsed:
                return parsed
    return None


def _ensure_sqlite_vec(connection: sqlite3.Connection):
    connection.enable_load_extension(True)
    try:
        import sqlite_vec  # type: ignore

        sqlite_vec.load(connection)
        return sqlite_vec
    except Exception as exc:  # pragma: no cover - runtime dependency error
        raise RuntimeError("Failed to load sqlite-vec extension") from exc


class SearchService:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self._sqlite_vec = _ensure_sqlite_vec(self.connection)
        self._init_schema()

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "SearchService":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _init_schema(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS sources (
                id TEXT PRIMARY KEY,
                canonical_domain TEXT NOT NULL UNIQUE,
                name TEXT,
                rss_feed TEXT
            );

            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                canonical_url TEXT NOT NULL UNIQUE,
                title TEXT,
                published_at TEXT,
                content_markdown TEXT NOT NULL,
                FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY,
                document_id TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                content_text TEXT NOT NULL,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
                UNIQUE (document_id, chunk_index)
            );

            CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts
            USING fts5(content_text, content='chunks', content_rowid='id', tokenize='porter');

            CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
                INSERT INTO chunks_fts(rowid, content_text)
                VALUES (new.id, new.content_text);
            END;

            CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
                INSERT INTO chunks_fts(chunks_fts, rowid, content_text)
                VALUES('delete', old.id, old.content_text);
            END;

            CREATE TRIGGER IF NOT EXISTS chunks_au AFTER UPDATE ON chunks BEGIN
                INSERT INTO chunks_fts(chunks_fts, rowid, content_text)
                VALUES('delete', old.id, old.content_text);
                INSERT INTO chunks_fts(rowid, content_text)
                VALUES (new.id, new.content_text);
            END;

            CREATE VIRTUAL TABLE IF NOT EXISTS chunks_vec
            USING vec0(embedding float[768]);

            CREATE TRIGGER IF NOT EXISTS chunks_vec_ad AFTER DELETE ON chunks BEGIN
                DELETE FROM chunks_vec WHERE rowid = old.id;
            END;
            """
        )
        self.connection.commit()

    def upsert_source(self, canonical_domain: str, name: Optional[str] = None, rss_feed: Optional[str] = None) -> Source:
        canonical_domain = canonical_domain.strip().lower()
        row = self.connection.execute(
            "SELECT id FROM sources WHERE canonical_domain = ?",
            (canonical_domain,),
        ).fetchone()
        if row:
            source_id = row["id"]
            self.connection.execute(
                "UPDATE sources SET name = ?, rss_feed = ? WHERE id = ?",
                (name, rss_feed, source_id),
            )
        else:
            source_id = source_id_for_domain(canonical_domain)
            self.connection.execute(
                "INSERT INTO sources (id, canonical_domain, name, rss_feed) VALUES (?, ?, ?, ?)",
                (source_id, canonical_domain, name, rss_feed),
            )
        self.connection.commit()
        return Source(id=source_id, canonical_domain=canonical_domain, name=name, rss_feed=rss_feed)

    def get_source(self, source_id: str) -> Optional[Source]:
        row = self.connection.execute(
            "SELECT id, canonical_domain, name, rss_feed FROM sources WHERE id = ?",
            (source_id,),
        ).fetchone()
        if not row:
            return None
        return Source(**dict(row))

    def list_sources(self) -> List[Source]:
        rows = self.connection.execute(
            "SELECT id, canonical_domain, name, rss_feed FROM sources ORDER BY canonical_domain"
        ).fetchall()
        return [Source(**dict(row)) for row in rows]

    def delete_source(self, source_id: str) -> bool:
        cursor = self.connection.execute("DELETE FROM sources WHERE id = ?", (source_id,))
        self.connection.commit()
        return cursor.rowcount > 0

    def _get_source_by_domain(self, canonical_domain: str) -> Optional[Source]:
        row = self.connection.execute(
            "SELECT id, canonical_domain, name, rss_feed FROM sources WHERE canonical_domain = ?",
            (canonical_domain,),
        ).fetchone()
        return Source(**dict(row)) if row else None

    def upsert_document(
        self,
        source_id: str,
        canonical_url: str,
        title: Optional[str],
        published_at: Optional[datetime],
        content_markdown: str,
    ) -> Document:
        canonical_url = _canonicalize_url(canonical_url)
        row = self.connection.execute(
            "SELECT id, content_markdown FROM documents WHERE canonical_url = ?",
            (canonical_url,),
        ).fetchone()
        content_changed = True
        if row:
            document_id = row["id"]
            content_changed = row["content_markdown"] != content_markdown
            self.connection.execute(
                """
                UPDATE documents
                SET source_id = ?, title = ?, published_at = ?, content_markdown = ?
                WHERE id = ?
                """,
                (
                    source_id,
                    title,
                    _serialize_datetime(published_at),
                    content_markdown,
                    document_id,
                ),
            )
        else:
            document_id = document_id_for_url(canonical_url)
            self.connection.execute(
                """
                INSERT INTO documents (id, source_id, canonical_url, title, published_at, content_markdown)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    document_id,
                    source_id,
                    canonical_url,
                    title,
                    _serialize_datetime(published_at),
                    content_markdown,
                ),
            )
        if content_changed:
            self.connection.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))
            self._create_chunks(document_id, content_markdown)
        self.connection.commit()
        return Document(
            id=document_id,
            source_id=source_id,
            canonical_url=canonical_url,
            title=title,
            published_at=published_at,
            content_markdown=content_markdown,
        )

    def get_document(self, document_id: str) -> Optional[Document]:
        row = self.connection.execute(
            """
            SELECT id, source_id, canonical_url, title, published_at, content_markdown
            FROM documents WHERE id = ?
            """,
            (document_id,),
        ).fetchone()
        if not row:
            return None
        data = dict(row)
        data["published_at"] = _parse_datetime(data["published_at"])
        return Document(**data)

    def list_documents(self, source_id: Optional[str] = None) -> List[Document]:
        if source_id:
            rows = self.connection.execute(
                """
                SELECT id, source_id, canonical_url, title, published_at, content_markdown
                FROM documents WHERE source_id = ? ORDER BY canonical_url
                """,
                (source_id,),
            ).fetchall()
        else:
            rows = self.connection.execute(
                """
                SELECT id, source_id, canonical_url, title, published_at, content_markdown
                FROM documents ORDER BY canonical_url
                """
            ).fetchall()
        documents = []
        for row in rows:
            data = dict(row)
            data["published_at"] = _parse_datetime(data["published_at"])
            documents.append(Document(**data))
        return documents

    def delete_document(self, document_id: str) -> bool:
        cursor = self.connection.execute("DELETE FROM documents WHERE id = ?", (document_id,))
        self.connection.commit()
        return cursor.rowcount > 0

    def _create_chunks(self, document_id: str, content_markdown: str) -> List[Chunk]:
        chunks = chunk_markdown(content_markdown)
        embeddings = embed_texts(chunks, prompt="search_document") if chunks else []
        created: List[Chunk] = []
        for index, content_text in enumerate(chunks):
            cursor = self.connection.execute(
                "INSERT INTO chunks (document_id, chunk_index, content_text) VALUES (?, ?, ?)",
                (document_id, index, content_text),
            )
            chunk_id = int(cursor.lastrowid)
            embedding = embeddings[index]
            self.connection.execute(
                "INSERT INTO chunks_vec (rowid, embedding) VALUES (?, ?)",
                (chunk_id, self._sqlite_vec.serialize_float32(embedding)),
            )
            created.append(
                Chunk(id=chunk_id, document_id=document_id, chunk_index=index, content_text=content_text)
            )
        return created

    def create_document_from_url(self, url: str) -> Document:
        response = httpx.get(url, timeout=20.0)
        response.raise_for_status()
        html = response.text
        canonical_url = _extract_canonical_url(html, url)
        canonical_domain = _normalize_domain(canonical_url)
        source = self._get_source_by_domain(canonical_domain)
        if not source:
            source = self.upsert_source(canonical_domain=canonical_domain, name=None, rss_feed=None)
        readable = ReadabilityDocument(html)
        content_html = readable.summary()
        content_markdown = html_to_markdown(content_html)
        title = readable.short_title() or None
        published_at = _extract_published_at(html)
        return self.upsert_document(
            source_id=source.id,
            canonical_url=canonical_url,
            title=title,
            published_at=published_at,
            content_markdown=content_markdown,
        )

    def create_documents_from_feed(self, feed_url: str) -> List[Document]:
        import feedparser

        feed = feedparser.parse(feed_url)
        documents: List[Document] = []
        for entry in feed.entries:
            entry_url = entry.get("link") or entry.get("id")
            if not entry_url:
                continue
            canonical_url = _canonicalize_url(entry_url)
            canonical_domain = _normalize_domain(canonical_url)
            source = self._get_source_by_domain(canonical_domain)
            if not source:
                source = self.upsert_source(
                    canonical_domain=canonical_domain,
                    name=feed.feed.get("title"),
                    rss_feed=feed_url,
                )
            content = None
            if entry.get("content"):
                content = entry.content[0].value
            content = content or entry.get("summary") or ""
            content_markdown = html_to_markdown(content)
            title = entry.get("title")
            published_at = _parse_datetime(entry.get("published") or entry.get("updated"))
            documents.append(
                self.upsert_document(
                    source_id=source.id,
                    canonical_url=canonical_url,
                    title=title,
                    published_at=published_at,
                    content_markdown=content_markdown,
                )
            )
        return documents

    def create_documents_from_opml(self, opml_url: str) -> List[Document]:
        """Fetch and parse OPML, then ingest documents from each feed URL with best-effort handling."""
        response = httpx.get(opml_url, timeout=20.0)
        response.raise_for_status()
        xml_content = response.text

        feed_urls = _extract_feed_urls_from_opml(xml_content)
        unique_urls = _dedupe_urls(feed_urls)

        all_documents: List[Document] = []
        for feed_url in unique_urls:
            try:
                docs = self.create_documents_from_feed(feed_url)
                all_documents.extend(docs)
            except Exception:
                # Best-effort: continue processing remaining feeds on failure
                continue

        return all_documents

    def create_documents_from_sitemap(self, sitemap_url: str) -> List[Document]:
        """Fetch and parse sitemap XML, then ingest each URL entry with best-effort handling."""
        response = httpx.get(sitemap_url, timeout=20.0)
        response.raise_for_status()
        xml_content = response.text

        page_urls = _extract_urls_from_sitemap(xml_content)
        unique_urls = _dedupe_urls(page_urls)

        documents: List[Document] = []
        for page_url in unique_urls:
            try:
                documents.append(self.create_document_from_url(page_url))
            except Exception:
                # Best-effort: continue processing remaining URLs on failure
                continue

        return documents

    def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        query = query.strip()
        if not query:
            return []
        if limit <= 0:
            return []

        candidate_limit = limit * 10
        query_embedding = embed_texts([query], prompt="search_query")[0]
        scored_rows = self.connection.execute(
            """
            WITH
            fts_top AS (
                SELECT
                    chunks.id AS chunk_id,
                    bm25(chunks_fts) AS rank
                FROM chunks_fts
                JOIN chunks ON chunks_fts.rowid = chunks.id
                WHERE chunks_fts MATCH ?
                ORDER BY rank ASC, chunks.id ASC
                LIMIT ?
            ),
            fts_ranked AS (
                SELECT
                    chunk_id,
                    1.0 / (1 + row_number() OVER (ORDER BY rank ASC, chunk_id ASC)) AS fts_score
                FROM fts_top
            ),
            vec_top AS (
                SELECT
                    rowid AS chunk_id,
                    distance
                FROM chunks_vec
                WHERE embedding MATCH ?
                ORDER BY distance ASC
                LIMIT ?
            ),
            vec_ranked AS (
                SELECT
                    chunk_id,
                    1.0 / (1 + row_number() OVER (ORDER BY distance ASC, chunk_id ASC)) AS vector_score
                FROM vec_top
            ),
            all_chunk_ids AS (
                SELECT chunk_id FROM fts_ranked
                UNION
                SELECT chunk_id FROM vec_ranked
            )
            SELECT
                all_chunk_ids.chunk_id,
                COALESCE(fts_ranked.fts_score, 0.0) AS fts_score,
                COALESCE(vec_ranked.vector_score, 0.0) AS vector_score,
                COALESCE(fts_ranked.fts_score, 0.0) + COALESCE(vec_ranked.vector_score, 0.0) AS final_score
            FROM all_chunk_ids
            LEFT JOIN fts_ranked ON fts_ranked.chunk_id = all_chunk_ids.chunk_id
            LEFT JOIN vec_ranked ON vec_ranked.chunk_id = all_chunk_ids.chunk_id
            ORDER BY final_score DESC, all_chunk_ids.chunk_id ASC
            LIMIT ?
            """,
            (
                query,
                candidate_limit,
                self._sqlite_vec.serialize_float32(query_embedding),
                candidate_limit,
                limit,
            ),
        ).fetchall()
        if not scored_rows:
            return []

        scores: dict[int, SearchScores] = {}
        ranked_chunk_ids: List[int] = []
        for row in scored_rows:
            chunk_id = row["chunk_id"]
            ranked_chunk_ids.append(chunk_id)
            scores[chunk_id] = SearchScores(
                fts=row["fts_score"],
                vector=row["vector_score"],
                hybrid=row["final_score"],
            )

        placeholders = ",".join(["?"] * len(ranked_chunk_ids))
        rows = self.connection.execute(
            f"""
            SELECT
                chunks.id AS chunk_id,
                chunks.document_id,
                chunks.chunk_index,
                chunks.content_text,
                documents.id AS document_id,
                documents.source_id,
                documents.canonical_url,
                documents.title,
                documents.published_at,
                documents.content_markdown
            FROM chunks
            JOIN documents ON documents.id = chunks.document_id
            WHERE chunks.id IN ({placeholders})
            """,
            tuple(ranked_chunk_ids),
        ).fetchall()

        rows_by_chunk_id = {row["chunk_id"]: row for row in rows}
        results: List[SearchResult] = []
        for chunk_id in ranked_chunk_ids:
            row = rows_by_chunk_id.get(chunk_id)
            if row is None:
                continue
            data = dict(row)
            chunk = Chunk(
                id=data["chunk_id"],
                document_id=data["document_id"],
                chunk_index=data["chunk_index"],
                content_text=data["content_text"],
            )
            document = Document(
                id=data["document_id"],
                source_id=data["source_id"],
                canonical_url=data["canonical_url"],
                title=data["title"],
                published_at=_parse_datetime(data["published_at"]),
                content_markdown=data["content_markdown"],
            )
            score = scores[chunk_id]
            results.append(
                SearchResult(
                    chunk=chunk,
                    document=document,
                    score=score.hybrid,
                    fts_score=score.fts,
                    vector_score=score.vector,
                )
            )

        return results
