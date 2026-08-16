import httpx
from langchain_core.documents import Document

import app.api.routes.chat as chat_module


class FakeMessage:
    def __init__(self, content):
        self.content = content


class FakeLLM:
    def invoke(self, prompt):
        return FakeMessage("90 días [contrato.pdf, pág. 4]")


class FakeVectorStoreWithResults:
    def similarity_search(self, query, k):
        return [
            (
                Document(
                    page_content="preaviso de 90 días",
                    metadata={"document_id": "d1", "source": "contrato.pdf", "page": 4},
                ),
                0.9,
            )
        ]


class FakeVectorStoreEmpty:
    def similarity_search(self, query, k):
        return []


def test_chat_with_indexed_documents(client, monkeypatch):
    monkeypatch.setattr(chat_module, "VectorStoreRepository", FakeVectorStoreWithResults)
    monkeypatch.setattr(chat_module, "get_llm", lambda model=None: FakeLLM())

    response = client.post("/chat", json={"message": "¿Cuál es el preaviso?"})

    assert response.status_code == 200
    body = response.json()
    assert "90 días" in body["answer"]
    assert body["sources"][0]["document_name"] == "contrato.pdf"


def test_chat_without_indexed_documents(client, monkeypatch):
    monkeypatch.setattr(chat_module, "VectorStoreRepository", FakeVectorStoreEmpty)
    monkeypatch.setattr(chat_module, "get_llm", lambda model=None: FakeLLM())

    response = client.post("/chat", json={"message": "¿Algo?"})

    assert response.status_code == 200
    body = response.json()
    assert body["sources"] == []
    assert "no tengo" in body["answer"].lower() or "no hay" in body["answer"].lower()


def test_chat_without_model_uses_default_from_settings(client, monkeypatch):
    import app.config as config_module

    monkeypatch.setattr(chat_module, "VectorStoreRepository", FakeVectorStoreEmpty)
    monkeypatch.setattr(chat_module, "get_llm", lambda model=None: FakeLLM())
    monkeypatch.setattr(config_module.settings, "ollama_model", "llama3.1:8b")

    response = client.post("/chat", json={"message": "¿Algo?"})

    assert response.json()["model"] == "llama3.1:8b"


def test_chat_with_explicit_model_overrides_default(client, monkeypatch):
    received = {}

    def fake_get_llm(model=None):
        received["model"] = model
        return FakeLLM()

    monkeypatch.setattr(chat_module, "VectorStoreRepository", FakeVectorStoreEmpty)
    monkeypatch.setattr(chat_module, "get_llm", fake_get_llm)

    response = client.post("/chat", json={"message": "¿Algo?", "model": "qwen2.5:7b"})

    assert response.json()["model"] == "qwen2.5:7b"
    assert received["model"] == "qwen2.5:7b"


def test_list_models_excludes_embedding_model(client, monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "models": [
                    {"name": "qwen2.5:14b"},
                    {"name": "llama3.1:8b"},
                    {"name": "nomic-embed-text:latest"},
                ]
            }

    class FakeAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def get(self, url):
            return FakeResponse()

    monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **k: FakeAsyncClient())

    response = client.get("/models")

    assert response.status_code == 200
    body = response.json()
    assert "nomic-embed-text:latest" not in body["models"]
    assert "qwen2.5:14b" in body["models"]


def test_list_models_unreachable_returns_503(client, monkeypatch):
    class FakeAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def get(self, url):
            raise httpx.ConnectError("boom")

    monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **k: FakeAsyncClient())

    response = client.get("/models")

    assert response.status_code == 503
