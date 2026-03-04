from __future__ import annotations

from functools import lru_cache
from typing import Iterable, List

from sentence_transformers import SentenceTransformer

_EMBEDDING_BATCH_SIZE = 8


@lru_cache(maxsize=1)
def _load_model() -> SentenceTransformer:
    return SentenceTransformer("nomic-ai/nomic-embed-text-v1", trust_remote_code=True)


def embed_texts(texts: Iterable[str], *, prompt: str) -> List[list[float]]:
    text_list = list(texts)
    if not text_list:
        return []

    model = _load_model()
    embeddings = []
    for start in range(0, len(text_list), _EMBEDDING_BATCH_SIZE):
        batch = text_list[start : start + _EMBEDDING_BATCH_SIZE]
        embeddings.extend(model.encode(batch, normalize_embeddings=True, prompt=prompt))
    return [embedding.tolist() for embedding in embeddings]
