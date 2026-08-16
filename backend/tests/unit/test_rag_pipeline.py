from langchain_core.documents import Document

from app.core.rag_pipeline import NO_DOCUMENTS_ANSWER, make_generate_step_stream, run_pipeline


class FakeVectorStore:
    def __init__(self, results):
        self._results = results

    def similarity_search(self, query, k):
        return self._results


class FakeMessage:
    def __init__(self, content):
        self.content = content


class FakeLLM:
    def __init__(self, answer):
        self._answer = answer
        self.last_prompt = None

    def invoke(self, prompt):
        self.last_prompt = prompt
        return FakeMessage(self._answer)


class FakeStreamingLLM:
    def __init__(self, chunks):
        self._chunks = chunks

    async def astream(self, prompt):
        for chunk in self._chunks:
            yield FakeMessage(chunk)


def test_pipeline_returns_answer_and_sources_when_documents_found():
    doc = Document(
        page_content="El preaviso mínimo es de 90 días.",
        metadata={"document_id": "doc-1", "source": "contrato.pdf", "page": 4},
    )
    vector_store = FakeVectorStore([(doc, 0.91)])
    llm = FakeLLM("La respuesta es 90 días [contrato.pdf, pág. 4]")

    answer, sources = run_pipeline("¿Cuál es el preaviso?", vector_store, llm, top_k=5)

    assert answer == "La respuesta es 90 días [contrato.pdf, pág. 4]"
    assert len(sources) == 1
    assert sources[0]["document_name"] == "contrato.pdf"
    assert sources[0]["similarity_score"] == 0.91
    assert "90 días" in llm.last_prompt


def test_pipeline_does_not_call_llm_without_indexed_documents():
    vector_store = FakeVectorStore([])
    llm = FakeLLM("no debería llamarse")

    answer, sources = run_pipeline("¿Algo?", vector_store, llm, top_k=5)

    assert answer == NO_DOCUMENTS_ANSWER
    assert sources == []
    assert llm.last_prompt is None


async def test_generate_step_stream_yields_chunks_in_order():
    llm = FakeStreamingLLM(["La ", "respuesta ", "es 90 días."])
    generate_step_stream = make_generate_step_stream(llm)

    chunks = [chunk async for chunk in generate_step_stream({"prompt": "¿Cuál es el preaviso?"})]

    assert chunks == ["La ", "respuesta ", "es 90 días."]
    assert "".join(chunks) == "La respuesta es 90 días."
