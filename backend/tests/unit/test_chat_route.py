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
    monkeypatch.setattr(chat_module, "get_llm", lambda: FakeLLM())

    response = client.post("/chat", json={"message": "¿Cuál es el preaviso?"})

    assert response.status_code == 200
    body = response.json()
    assert "90 días" in body["answer"]
    assert body["sources"][0]["document_name"] == "contrato.pdf"


def test_chat_without_indexed_documents(client, monkeypatch):
    monkeypatch.setattr(chat_module, "VectorStoreRepository", FakeVectorStoreEmpty)
    monkeypatch.setattr(chat_module, "get_llm", lambda: FakeLLM())

    response = client.post("/chat", json={"message": "¿Algo?"})

    assert response.status_code == 200
    body = response.json()
    assert body["sources"] == []
    assert "no tengo" in body["answer"].lower() or "no hay" in body["answer"].lower()
