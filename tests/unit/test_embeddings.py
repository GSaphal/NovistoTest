import pytest

import app.embeddings as embeddings_module

pytestmark = pytest.mark.unit


class _FakeEmbeddingData:
    def __init__(self, vector):
        self.embedding = vector


class _FakeResponse:
    def __init__(self, vectors):
        self.data = [_FakeEmbeddingData(v) for v in vectors]


class _FakeEmbeddingsAPI:
    def __init__(self, response):
        self._response = response
        self.calls = []

    def create(self, model, input):
        self.calls.append(input)
        return self._response


class _FakeClient:
    def __init__(self, response):
        self.embeddings = _FakeEmbeddingsAPI(response)


def test_embed_batch_preserves_order(monkeypatch):
    fake_client = _FakeClient(_FakeResponse([[0.1, 0.2], [0.3, 0.4]]))
    monkeypatch.setattr(embeddings_module, "_get_client", lambda: fake_client)

    result = embeddings_module.embed_batch(["first text", "second text"])

    assert fake_client.embeddings.calls == [["first text", "second text"]]
    assert result == [[0.1, 0.2], [0.3, 0.4]]


def test_embed_batch_empty_input_makes_no_network_call(monkeypatch):
    def fail_if_called():
        raise AssertionError("should not even construct a client for empty input")

    monkeypatch.setattr(embeddings_module, "_get_client", fail_if_called)

    assert embeddings_module.embed_batch([]) == []