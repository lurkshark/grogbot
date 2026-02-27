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
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    content_markdown: str


class Chunk(BaseModel):
    id: int
    document_id: str
    chunk_index: int
    content_text: str


class SearchResult(BaseModel):
    chunk: Chunk
    document: Document
    score: float = Field(..., description="Hybrid score combining FTS and vector similarity")
    fts_score: float
    vector_score: float
