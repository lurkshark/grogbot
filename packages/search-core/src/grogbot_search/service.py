from __future__ import annotations

import hashlib
import html
import re
import time
import pysqlite3 as sqlite3
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional
from urllib.parse import parse_qs, urlencode, urlparse, urljoin, urlunparse

import httpx
import markdown
from bs4 import BeautifulSoup
from dateutil import parser as date_parser
from markdownify import markdownify as html_to_markdown
from readability import Document as ReadabilityDocument

from grogbot_search.chunking import chunk_markdown
from grogbot_search.embeddings import embed_texts
from grogbot_search.ids import document_id_for_url, source_id_for_domain
from grogbot_search.models import Chunk, Document, SearchResult, Source


@dataclass
class SearchScores:
    fts: float
    vector: float
    link: float
    hybrid: float


_BACKOFF_STATUS_CODES = {401, 403, 429, 503}
_CAPTCHA_MARKERS = (
    "cf-chl",
    "recaptcha",
    "attention required",
    "verify you are human",
)

_DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; Grogbot/1.0; +https://www.hauntedspice.com)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Upgrade-Insecure-Requests": "1",
}


class BackoffError(RuntimeError):
    """Raised when URL ingestion encounters a backoff or anti-bot signal."""


class DocumentNotFoundError(RuntimeError):
    """Raised when a document id is not found for chunking operations."""


def _classify_backoff_response(response: httpx.Response) -> Optional[str]:
    if response.status_code in _BACKOFF_STATUS_CODES:
        return f"status_code={response.status_code}"

    if response.headers.get("Retry-After") is not None:
        return "retry-after-header"

    body_match = re.search(r"<body\b[^>]*>(.*?)</body>", response.text, flags=re.IGNORECASE | re.DOTALL)
    body = (body_match.group(1) if body_match else "").lower()
    for marker in _CAPTCHA_MARKERS:
        if marker in body:
            return f"body-marker={marker}"

    return None


def _normalize_domain(url: str) -> str:
    return urlparse(url).netloc.lower()


def _canonicalize_url(url: str) -> str:
    return url.strip()


def _content_hash(content_markdown: str) -> str:
    return hashlib.sha256(content_markdown.encode("utf-8")).hexdigest()[:6]


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


def _extract_markdown_links(content_markdown: str) -> List[str]:
    rendered_html = markdown.markdown(content_markdown)
    soup = BeautifulSoup(rendered_html, "html.parser")
    links: List[str] = []
    for anchor in soup.find_all("a", href=True):
        href = _canonicalize_url(str(anchor.get("href") or ""))
        if href:
            links.append(href)
    return links


def _to_document_ids_from_markdown(
    *,
    source_document_id: str,
    source_canonical_url: str,
    content_markdown: str,
) -> set[str]:
    to_document_ids: set[str] = set()
    source_domain = _normalize_domain(_canonicalize_url(source_canonical_url))
    for href in _extract_markdown_links(content_markdown):
        resolved_url = _canonicalize_url(urljoin(source_canonical_url, href))
        if not resolved_url:
            continue
        if _normalize_domain(resolved_url) == source_domain:
            continue
        to_document_id = document_id_for_url(_canonicalize_url(resolved_url))
        if to_document_id == source_document_id:
            continue
        to_document_ids.add(to_document_id)
    return to_document_ids


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
        self._http_client = httpx.Client(headers=_DEFAULT_HEADERS)
        self._init_schema()

    def _http_get(self, url: str, timeout: float = 20.0) -> httpx.Response:
        # Keep a single in-memory cookie jar for non-feed requests during this service run.
        return self._http_client.get(url, timeout=timeout)

    def close(self) -> None:
        self._http_client.close()
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
                content_hash TEXT NOT NULL
                    CHECK (length(content_hash) = 6)
                    CHECK (content_hash GLOB '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'),
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

            CREATE TABLE IF NOT EXISTS links (
                from_document_id TEXT NOT NULL,
                to_document_id TEXT NOT NULL,
                PRIMARY KEY (from_document_id, to_document_id),
                FOREIGN KEY (from_document_id) REFERENCES documents(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_links_to_document_id ON links (to_document_id);

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
        self._migrate_legacy_documents_table()
        self.connection.commit()

    def _migrate_legacy_documents_table(self) -> None:
        columns = {
            row["name"]
            for row in self.connection.execute("PRAGMA table_info(documents)").fetchall()
        }
        if "content_markdown" not in columns or "content_hash" in columns:
            return

        legacy_rows = self.connection.execute(
            """
            SELECT id, source_id, canonical_url, title, published_at, content_markdown
            FROM documents
            ORDER BY id
            """
        ).fetchall()

        self.connection.commit()
        self.connection.execute("PRAGMA foreign_keys = OFF")
        try:
            self.connection.execute("BEGIN")
            self.connection.executescript(
                """
                ALTER TABLE documents RENAME TO documents_legacy;

                CREATE TABLE documents (
                    id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    canonical_url TEXT NOT NULL UNIQUE,
                    title TEXT,
                    published_at TEXT,
                    content_hash TEXT NOT NULL
                        CHECK (length(content_hash) = 6)
                        CHECK (content_hash GLOB '[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'),
                    FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE CASCADE
                );
                """
            )

            for row in legacy_rows:
                self.connection.execute(
                    """
                    INSERT INTO documents (id, source_id, canonical_url, title, published_at, content_hash)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row["id"],
                        row["source_id"],
                        row["canonical_url"],
                        row["title"],
                        row["published_at"],
                        _content_hash(row["content_markdown"]),
                    ),
                )

            self.connection.execute("DROP TABLE documents_legacy")
            self.connection.execute("COMMIT")
        except Exception:
            self.connection.execute("ROLLBACK")
            raise
        finally:
            self.connection.execute("PRAGMA foreign_keys = ON")

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
        if not content_markdown or not content_markdown.strip():
            raise ValueError("content_markdown cannot be empty")

        canonical_url = _canonicalize_url(canonical_url)
        new_content_hash = _content_hash(content_markdown)

        row = self.connection.execute(
            "SELECT id, content_hash FROM documents WHERE canonical_url = ?",
            (canonical_url,),
        ).fetchone()

        content_changed = True
        if row:
            document_id = row["id"]
            content_changed = row["content_hash"] != new_content_hash
            self.connection.execute(
                """
                UPDATE documents
                SET source_id = ?, title = ?, published_at = ?, content_hash = ?
                WHERE id = ?
                """,
                (
                    source_id,
                    title,
                    _serialize_datetime(published_at),
                    new_content_hash,
                    document_id,
                ),
            )
        else:
            document_id = document_id_for_url(canonical_url)
            self.connection.execute(
                """
                INSERT INTO documents (id, source_id, canonical_url, title, published_at, content_hash)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    document_id,
                    source_id,
                    canonical_url,
                    title,
                    _serialize_datetime(published_at),
                    new_content_hash,
                ),
            )

        if content_changed:
            self.connection.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))
            self.connection.execute("DELETE FROM links WHERE from_document_id = ?", (document_id,))
            self._insert_plaintext_chunks(document_id=document_id, content_markdown=content_markdown)
            self._insert_document_links(
                document_id=document_id,
                source_canonical_url=canonical_url,
                content_markdown=content_markdown,
            )

        self.connection.commit()
        return Document(
            id=document_id,
            source_id=source_id,
            canonical_url=canonical_url,
            title=title,
            published_at=published_at,
            content_hash=new_content_hash,
        )

    def get_document(self, document_id: str) -> Optional[Document]:
        row = self.connection.execute(
            """
            SELECT id, source_id, canonical_url, title, published_at, content_hash
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
                SELECT id, source_id, canonical_url, title, published_at, content_hash
                FROM documents WHERE source_id = ? ORDER BY canonical_url
                """,
                (source_id,),
            ).fetchall()
        else:
            rows = self.connection.execute(
                """
                SELECT id, source_id, canonical_url, title, published_at, content_hash
                FROM documents ORDER BY canonical_url
                """
            ).fetchall()
        documents = []
        for row in rows:
            data = dict(row)
            data["published_at"] = _parse_datetime(data["published_at"])
            documents.append(Document(**data))
        return documents

    def document_has_chunks(self, document_id: str) -> bool:
        row = self.connection.execute(
            "SELECT 1 FROM chunks WHERE document_id = ? LIMIT 1",
            (document_id,),
        ).fetchone()
        return row is not None

    def delete_document(self, document_id: str) -> bool:
        cursor = self.connection.execute("DELETE FROM documents WHERE id = ?", (document_id,))
        self.connection.commit()
        return cursor.rowcount > 0

    def embed_document_chunks(self, document_id: str) -> int:
        if not self.get_document(document_id):
            raise DocumentNotFoundError(f"Document not found: {document_id}")

        rows = self.connection.execute(
            """
            SELECT chunks.id, chunks.content_text
            FROM chunks
            LEFT JOIN chunks_vec ON chunks_vec.rowid = chunks.id
            WHERE chunks.document_id = ? AND chunks_vec.rowid IS NULL
            ORDER BY chunks.chunk_index
            """,
            (document_id,),
        ).fetchall()
        if not rows:
            return 0

        texts = [row["content_text"] for row in rows]
        embeddings = embed_texts(texts, prompt="search_document")
        for row, embedding in zip(rows, embeddings):
            self.connection.execute(
                "INSERT INTO chunks_vec (rowid, embedding) VALUES (?, ?)",
                (row["id"], self._sqlite_vec.serialize_float32(embedding)),
            )
        self.connection.commit()
        return len(rows)

    def synchronize_document_embeddings(self, maximum: Optional[int] = None) -> int:
        if maximum is not None and maximum <= 0:
            return 0

        query = (
            "SELECT documents.id "
            "FROM documents "
            "JOIN chunks ON chunks.document_id = documents.id "
            "LEFT JOIN chunks_vec ON chunks_vec.rowid = chunks.id "
            "WHERE chunks_vec.rowid IS NULL "
            "GROUP BY documents.id "
            "ORDER BY documents.id"
        )
        params: tuple = ()
        if maximum is not None:
            query = f"{query} LIMIT ?"
            params = (maximum,)
        rows = self.connection.execute(query, params).fetchall()

        total_created = 0
        for row in rows:
            total_created += self.embed_document_chunks(row["id"])
        return total_created

    # Backwards-compatible aliases.
    def chunk_document(self, document_id: str) -> int:
        return self.embed_document_chunks(document_id)

    def synchronize_document_chunks(self, maximum: Optional[int] = None) -> int:
        return self.synchronize_document_embeddings(maximum=maximum)

    def _insert_document_links(self, *, document_id: str, source_canonical_url: str, content_markdown: str) -> None:
        to_document_ids = _to_document_ids_from_markdown(
            source_document_id=document_id,
            source_canonical_url=source_canonical_url,
            content_markdown=content_markdown,
        )
        for to_document_id in sorted(to_document_ids):
            self.connection.execute(
                "INSERT OR IGNORE INTO links (from_document_id, to_document_id) VALUES (?, ?)",
                (document_id, to_document_id),
            )

    def _insert_plaintext_chunks(self, *, document_id: str, content_markdown: str) -> List[Chunk]:
        chunks = chunk_markdown(content_markdown)
        created: List[Chunk] = []
        for index, content_text in enumerate(chunks):
            cursor = self.connection.execute(
                "INSERT INTO chunks (document_id, chunk_index, content_text) VALUES (?, ?, ?)",
                (document_id, index, content_text),
            )
            chunk_id = int(cursor.lastrowid)
            created.append(
                Chunk(id=chunk_id, document_id=document_id, chunk_index=index, content_text=content_text)
            )
        return created

    def create_document_from_url(self, url: str) -> Document:
        response = self._http_get(url, timeout=20.0)
        backoff_reason = _classify_backoff_response(response)
        if backoff_reason:
            raise BackoffError(f"Backoff detected while ingesting URL {url}: {backoff_reason}")
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
        if not content_markdown or not content_markdown.strip():
            raise ValueError(f"Empty content for URL {canonical_url}")
        title = readable.short_title() or None
        published_at = _extract_published_at(html)
        return self.upsert_document(
            source_id=source.id,
            canonical_url=canonical_url,
            title=title,
            published_at=published_at,
            content_markdown=content_markdown,
        )

    def create_documents_from_feed(self, feed_url: str, paginate: bool = False) -> List[Document]:
        import feedparser

        def _next_feed_url(parsed_feed, base_url: str) -> Optional[str]:
            for link in parsed_feed.feed.get("links") or []:
                if link.get("rel") != "next":
                    continue
                href = link.get("href") or link.get("url")
                if href:
                    return _canonicalize_url(urljoin(base_url, href))
            return None

        def _is_wordpress_feed(parsed_feed) -> bool:
            generator = parsed_feed.feed.get("generator")
            if isinstance(generator, dict):
                generator = generator.get("value") or generator.get("name")
            if isinstance(generator, str):
                return "wordpress" in generator.lower()
            return False

        def _next_wordpress_url(base_url: str) -> Optional[str]:
            parsed_url = urlparse(base_url)
            query_params = parse_qs(parsed_url.query, keep_blank_values=True)
            current_page = 1
            if "paged" in query_params and query_params["paged"]:
                try:
                    current_page = int(query_params["paged"][-1])
                except (TypeError, ValueError):
                    current_page = 1
            query_params["paged"] = [str(current_page + 1)]
            next_query = urlencode(query_params, doseq=True)
            return _canonicalize_url(urlunparse(parsed_url._replace(query=next_query)))

        documents: List[Document] = []
        seen_feed_urls: set[str] = set()
        current_url = feed_url
        feed_name: Optional[str] = None
        pages_processed = 0

        while current_url:
            normalized_url = _canonicalize_url(current_url)
            if normalized_url in seen_feed_urls:
                break
            seen_feed_urls.add(normalized_url)
            pages_processed += 1

            start_time = time.monotonic() if paginate else None
            try:
                try:
                    feed = feedparser.parse(current_url)
                except Exception:
                    if pages_processed == 1:
                        raise
                    break

                if pages_processed > 1:
                    status = getattr(feed, "status", None)
                    if status is not None and status >= 400:
                        break
                    if getattr(feed, "bozo", 0) and not feed.entries:
                        break

                page_feed_name = feed.feed.get("title")
                if page_feed_name:
                    feed_name = feed_name or page_feed_name

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
                            name=feed_name,
                            rss_feed=feed_url,
                        )
                    else:
                        updated_name = source.name or feed_name
                        updated_rss_feed = source.rss_feed or feed_url
                        if updated_name != source.name or updated_rss_feed != source.rss_feed:
                            source = self.upsert_source(
                                canonical_domain=canonical_domain,
                                name=updated_name,
                                rss_feed=updated_rss_feed,
                            )
                    content = None
                    if entry.get("content"):
                        content = entry.content[0].value
                    content = content or entry.get("summary") or ""
                    content_markdown = html_to_markdown(content)
                    if not content_markdown or not content_markdown.strip():
                        continue
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

                if not paginate:
                    break
                if pages_processed >= 100:
                    break

                next_url = _next_feed_url(feed, current_url)
                if not next_url and _is_wordpress_feed(feed):
                    next_url = _next_wordpress_url(current_url)
                if not next_url:
                    break
                current_url = next_url
            finally:
                if start_time is not None:
                    elapsed = time.monotonic() - start_time
                    if elapsed < 1.0:
                        time.sleep(1.0 - elapsed)

        return documents

    def create_documents_from_opml(self, opml_url: str, paginate: bool = False) -> List[Document]:
        """Fetch and parse OPML, then ingest documents from each feed URL with best-effort handling."""
        response = self._http_get(opml_url, timeout=20.0)
        response.raise_for_status()
        xml_content = response.text

        feed_urls = _extract_feed_urls_from_opml(xml_content)
        unique_urls = _dedupe_urls(feed_urls)

        all_documents: List[Document] = []
        for feed_url in unique_urls:
            try:
                docs = self.create_documents_from_feed(feed_url, paginate=paginate)
                all_documents.extend(docs)
            except Exception:
                # Best-effort: continue processing remaining feeds on failure
                continue

        return all_documents

    def create_documents_from_sitemap(self, sitemap_url: str, bootstrap: bool = False) -> List[Document]:
        """Fetch and parse sitemap XML, then ingest each URL entry with best-effort handling."""
        response = self._http_get(sitemap_url, timeout=20.0)
        response.raise_for_status()
        xml_content = response.text

        page_urls = _extract_urls_from_sitemap(xml_content)
        unique_urls = _dedupe_urls(page_urls)

        documents: List[Document] = []
        for page_url in unique_urls:
            canonical_url = _canonicalize_url(page_url)
            if bootstrap:
                existing = self.connection.execute(
                    "SELECT 1 FROM documents WHERE canonical_url = ? LIMIT 1",
                    (canonical_url,),
                ).fetchone()
                if existing:
                    continue

            start_time = time.monotonic()
            try:
                documents.append(self.create_document_from_url(page_url))
            except BackoffError:
                # Fail-fast for explicit backoff/anti-bot signals
                raise
            except Exception:
                # Best-effort: continue processing remaining URLs on failure
                continue
            finally:
                elapsed = time.monotonic() - start_time
                if elapsed < 1.0:
                    time.sleep(1.0 - elapsed)

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
            ),
            candidate_documents AS (
                SELECT DISTINCT chunks.document_id
                FROM all_chunk_ids
                JOIN chunks ON chunks.id = all_chunk_ids.chunk_id
            ),
            candidate_inbound_links AS (
                SELECT
                    candidate_documents.document_id,
                    COUNT(links.from_document_id) AS inbound_count
                FROM candidate_documents
                LEFT JOIN links ON links.to_document_id = candidate_documents.document_id
                GROUP BY candidate_documents.document_id
            ),
            link_ranked AS (
                SELECT
                    document_id,
                    1.0 / (1 + row_number() OVER (ORDER BY inbound_count DESC, document_id ASC)) AS link_score
                FROM candidate_inbound_links
                WHERE inbound_count > 0
            )
            SELECT
                all_chunk_ids.chunk_id,
                COALESCE(fts_ranked.fts_score, 0.0) AS fts_score,
                COALESCE(vec_ranked.vector_score, 0.0) AS vector_score,
                COALESCE(link_ranked.link_score, 0.0) AS link_score,
                COALESCE(fts_ranked.fts_score, 0.0)
                    + COALESCE(vec_ranked.vector_score, 0.0)
                    + COALESCE(link_ranked.link_score, 0.0) AS final_score
            FROM all_chunk_ids
            JOIN chunks ON chunks.id = all_chunk_ids.chunk_id
            LEFT JOIN fts_ranked ON fts_ranked.chunk_id = all_chunk_ids.chunk_id
            LEFT JOIN vec_ranked ON vec_ranked.chunk_id = all_chunk_ids.chunk_id
            LEFT JOIN link_ranked ON link_ranked.document_id = chunks.document_id
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
                link=row["link_score"],
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
                documents.content_hash
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
                content_hash=data["content_hash"],
            )
            score = scores[chunk_id]
            results.append(
                SearchResult(
                    chunk=chunk,
                    document=document,
                    score=score.hybrid,
                    fts_score=score.fts,
                    vector_score=score.vector,
                    link_score=score.link,
                )
            )

        return results
