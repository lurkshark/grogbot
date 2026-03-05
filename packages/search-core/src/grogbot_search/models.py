from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Source(BaseModel):
    id: str
    canonical_domain: str
    name: Optional[str] = None
    rss_feed: Optional[str] = None


class Document(BaseModel):
    id: str
    source_id: str
    canonical_url: str
    title: Optional[str] = None
    published_at: Optional[datetime] = None
    content_hash: str


class Chunk(BaseModel):
    id: int
    document_id: str
    chunk_index: int
    content_text: str


class SearchResult(BaseModel):
    chunk: Chunk
    document: Document
    score: float = Field(..., description="Final rank-fusion score combining FTS, vector, and link rankings")
    fts_score: float
    vector_score: float
    link_score: float


class DatasetStatistics(BaseModel):
    total_sources: int
    total_documents: int
    total_chunks: int
    total_links: int
    embedded_chunks: int
    embedding_progress: float = Field(..., description="Percentage of chunks with embeddings (0-100).")
    avg_chunks_per_document: float = Field(..., description="Average number of chunks per document.")
    documents_per_source: float = Field(..., description="Average number of documents per source.")
