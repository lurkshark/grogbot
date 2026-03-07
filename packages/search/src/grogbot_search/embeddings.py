from __future__ import annotations

from functools import lru_cache
from typing import Iterable, List

from sentence_transformers import SentenceTransformer


@lru_cache(maxsize=1)
def _load_model() -> SentenceTransformer:
    return SentenceTransformer("nomic-ai/nomic-embed-text-v1", trust_remote_code=True)


def embed_texts(texts: Iterable[str], *, prompt: str) -> List[list[float]]:
    text_list = list(texts)
    if not text_list:
        return []

    model = _load_model()
    embeddings = model.encode(
        text_list,
        batch_size=8,
        normalize_embeddings=True,
        prompt=prompt,
    )
    return [embedding.tolist() for embedding in embeddings]
