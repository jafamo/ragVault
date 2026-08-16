import json

import httpx
from langchain_core.documents import Document

import app.api.routes.chat as chat_module
from app.main import app


class FakeMessage:
    def __init__(self, content):
        self.content = content


class FakeLLM:
    def __init__(self, chunks=None, title="Título generado"):
        self._chunks = chunks if chunks is not None else ["90 días [contrato.pdf, pág. 4]"]
        self._title = title

    async def astream(self, prompt):
        for chunk in self._chunks:
            yield FakeMessage(chunk)

    def invoke(self, prompt):
        return FakeMessage(self._title)


class FailingLLM:
    async def astream(self, prompt):
        yield FakeMessage("empieza a responder... ")
        raise RuntimeError("Ollama se ha caído a mitad de generación")


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


class FailingVectorStore:
    def similarity_search(self, query, k):
        raise RuntimeError("ChromaDB no disponible")


def _new_session(client) -> str:
    return client.post("/sessions").json()["id"]


def _parse_sse(text: str) -> list[tuple[str, object]]:
    events: list[tuple[str, object]] = []
    for frame in text.split("\n\n"):
        if not frame.strip():
            continue
        event_line, data_line = frame.split("\n", 1)
        event = event_line.removeprefix("event: ")
        data = json.loads(data_line.removeprefix("data: "))
        events.append((event, data))
    return events


async def _post_chat(**json_body) -> tuple[int, list[tuple[str, object]]]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as async_client:
        response = await async_client.post("/chat", json=json_body)
        return response.status_code, (_parse_sse(response.text) if response.status_code == 200 else [])


async def test_chat_with_indexed_documents(client, monkeypatch):
    monkeypatch.setattr(chat_module, "VectorStoreRepository", FakeVectorStoreWithResults)
    monkeypatch.setattr(chat_module, "get_llm", lambda model=None: FakeLLM())
    session_id = _new_session(client)

    status, events = await _post_chat(message="¿Cuál es el preaviso?", session_id=session_id)

    assert status == 200
    chunk_events = [data for event, data in events if event == "chunk"]
    done_events = [data for event, data in events if event == "done"]
    assert "".join(chunk_events) == "90 días [contrato.pdf, pág. 4]"
    assert len(done_events) == 1
    assert done_events[0]["sources"][0]["document_name"] == "contrato.pdf"


async def test_chat_without_indexed_documents(client, monkeypatch):
    monkeypatch.setattr(chat_module, "VectorStoreRepository", FakeVectorStoreEmpty)
    monkeypatch.setattr(chat_module, "get_llm", lambda model=None: FakeLLM())
    session_id = _new_session(client)

    status, events = await _post_chat(message="¿Algo?", session_id=session_id)

    assert status == 200
    chunk_text = "".join(data for event, data in events if event == "chunk")
    done_events = [data for event, data in events if event == "done"]
    assert "no tengo" in chunk_text.lower() or "no hay" in chunk_text.lower()
    assert done_events[0]["sources"] == []


async def test_chat_without_model_uses_default_from_settings(client, monkeypatch):
    import app.config as config_module

    monkeypatch.setattr(chat_module, "VectorStoreRepository", FakeVectorStoreEmpty)
    monkeypatch.setattr(chat_module, "get_llm", lambda model=None: FakeLLM())
    monkeypatch.setattr(config_module.settings, "ollama_model", "llama3.1:8b")
    session_id = _new_session(client)

    status, events = await _post_chat(message="¿Algo?", session_id=session_id)

    done_events = [data for event, data in events if event == "done"]
    assert done_events[0]["model"] == "llama3.1:8b"


async def test_chat_with_explicit_model_overrides_default(client, monkeypatch):
    received = {}

    def fake_get_llm(model=None):
        received["model"] = model
        return FakeLLM()

    monkeypatch.setattr(chat_module, "VectorStoreRepository", FakeVectorStoreEmpty)
    monkeypatch.setattr(chat_module, "get_llm", fake_get_llm)
    session_id = _new_session(client)

    status, events = await _post_chat(
        message="¿Algo?", session_id=session_id, model="qwen2.5:7b"
    )

    done_events = [data for event, data in events if event == "done"]
    assert done_events[0]["model"] == "qwen2.5:7b"
    assert received["model"] == "qwen2.5:7b"


def test_chat_without_session_id_is_rejected(client, monkeypatch):
    monkeypatch.setattr(chat_module, "VectorStoreRepository", FakeVectorStoreEmpty)
    monkeypatch.setattr(chat_module, "get_llm", lambda model=None: FakeLLM())

    response = client.post("/chat", json={"message": "¿Algo?"})

    assert response.status_code == 422


def test_chat_with_unknown_session_id_is_rejected(client, monkeypatch):
    monkeypatch.setattr(chat_module, "VectorStoreRepository", FakeVectorStoreEmpty)
    monkeypatch.setattr(chat_module, "get_llm", lambda model=None: FakeLLM())

    response = client.post("/chat", json={"message": "¿Algo?", "session_id": "no-existe"})

    assert response.status_code == 404


async def test_chat_retrieval_failure_returns_503_without_opening_stream(client, monkeypatch):
    monkeypatch.setattr(chat_module, "VectorStoreRepository", FailingVectorStore)
    monkeypatch.setattr(chat_module, "get_llm", lambda model=None: FakeLLM())
    session_id = _new_session(client)

    status, events = await _post_chat(message="¿Algo?", session_id=session_id)

    assert status == 503
    assert events == []
    messages = client.get(f"/sessions/{session_id}/messages").json()
    assert [m["role"] for m in messages] == ["user"]


async def test_chat_generation_failure_emits_error_event_without_persisting_assistant(
    client, monkeypatch
):
    monkeypatch.setattr(chat_module, "VectorStoreRepository", FakeVectorStoreWithResults)
    monkeypatch.setattr(chat_module, "get_llm", lambda model=None: FailingLLM())
    session_id = _new_session(client)

    status, events = await _post_chat(message="¿Cuál es el preaviso?", session_id=session_id)

    assert status == 200
    assert events[-1][0] == "error"
    messages = client.get(f"/sessions/{session_id}/messages").json()
    assert [m["role"] for m in messages] == ["user"]


async def test_chat_persists_user_and_assistant_messages(client, monkeypatch):
    monkeypatch.setattr(chat_module, "VectorStoreRepository", FakeVectorStoreWithResults)
    monkeypatch.setattr(chat_module, "get_llm", lambda model=None: FakeLLM())
    session_id = _new_session(client)

    await _post_chat(message="¿Cuál es el preaviso?", session_id=session_id)

    messages = client.get(f"/sessions/{session_id}/messages").json()
    assert [m["role"] for m in messages] == ["user", "assistant"]
    assert messages[0]["content"] == "¿Cuál es el preaviso?"
    assert "90 días" in messages[1]["content"]
    assert messages[1]["model_used"] is not None
    assert "chunks_used" in messages[1]["sources"]


async def test_chat_generates_title_on_first_message_only(client, monkeypatch):
    monkeypatch.setattr(chat_module, "VectorStoreRepository", FakeVectorStoreEmpty)
    monkeypatch.setattr(chat_module, "get_llm", lambda model=None: FakeLLM())
    session_id = _new_session(client)
    assert client.get(f"/sessions/{session_id}").json()["title"] is None

    await _post_chat(message="primera pregunta", session_id=session_id)
    title_after_first = client.get(f"/sessions/{session_id}").json()["title"]
    assert title_after_first

    await _post_chat(message="segunda pregunta", session_id=session_id)
    title_after_second = client.get(f"/sessions/{session_id}").json()["title"]
    assert title_after_second == title_after_first


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
