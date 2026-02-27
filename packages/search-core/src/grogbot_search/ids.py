from __future__ import annotations

import hashlib
from slugify import slugify


def _slug_hash(value: str, prefix: str) -> str:
    normalized = value.strip().lower()
    slug = slugify(normalized)[:50].strip("-") or prefix
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:6]
    return f"{slug}-{digest}"


def source_id_for_domain(domain: str) -> str:
    return _slug_hash(domain, "source")


def document_id_for_url(url: str) -> str:
    return _slug_hash(url, "document")
