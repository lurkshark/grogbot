from __future__ import annotations

import grogbot_search.embeddings as embeddings


class _FakeArray:
    def __init__(self, values):
        self._values = values

    def tolist(self):
        return list(self._values)


def test_load_model_uses_expected_sentence_transformer(monkeypatch):
    calls: list[tuple[str, bool]] = []
    model = object()

    def fake_sentence_transformer(model_name: str, trust_remote_code: bool):
        calls.append((model_name, trust_remote_code))
        return model

    monkeypatch.setattr(embeddings, "SentenceTransformer", fake_sentence_transformer)
    embeddings._load_model.cache_clear()

    first = embeddings._load_model()
    second = embeddings._load_model()

    assert first is model
    assert second is model
    assert calls == [("nomic-ai/nomic-embed-text-v1", True)]

    embeddings._load_model.cache_clear()


def test_embed_texts_calls_model_and_returns_lists(monkeypatch):
    class FakeModel:
        def __init__(self):
            self.calls = []

        def encode(self, texts, *, normalize_embeddings: bool, prompt: str):
            self.calls.append((texts, normalize_embeddings, prompt))
            return [_FakeArray([1.0, 2.0]), _FakeArray([3.0, 4.0])]

    fake_model = FakeModel()
    monkeypatch.setattr(embeddings, "_load_model", lambda: fake_model)

    result = embeddings.embed_texts(("first", "second"), prompt="search_query")

    assert result == [[1.0, 2.0], [3.0, 4.0]]
    assert fake_model.calls == [(["first", "second"], True, "search_query")]


def test_embed_texts_batches_requests_to_max_eight(monkeypatch):
    class FakeModel:
        def __init__(self):
            self.calls = []

        def encode(self, texts, *, normalize_embeddings: bool, prompt: str):
            self.calls.append((list(texts), normalize_embeddings, prompt))
            return [_FakeArray([float(int(text.removeprefix("chunk-")))]) for text in texts]

    fake_model = FakeModel()
    monkeypatch.setattr(embeddings, "_load_model", lambda: fake_model)

    inputs = [f"chunk-{index}" for index in range(10)]
    result = embeddings.embed_texts(inputs, prompt="search_document")

    assert result == [[float(index)] for index in range(10)]
    assert fake_model.calls == [
        ([f"chunk-{index}" for index in range(8)], True, "search_document"),
        (["chunk-8", "chunk-9"], True, "search_document"),
    ]
