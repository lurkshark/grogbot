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

        def encode(self, texts, *, batch_size: int, normalize_embeddings: bool, prompt: str):
            self.calls.append((texts, batch_size, normalize_embeddings, prompt))
            return [_FakeArray([1.0, 2.0]), _FakeArray([3.0, 4.0])]

    fake_model = FakeModel()
    monkeypatch.setattr(embeddings, "_load_model", lambda: fake_model)

    result = embeddings.embed_texts(("first", "second"), prompt="search_query")

    assert result == [[1.0, 2.0], [3.0, 4.0]]
    assert fake_model.calls == [(["first", "second"], 8, True, "search_query")]
