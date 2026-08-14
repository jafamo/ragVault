from langchain_core.documents import Document

import app.document_processing.ingestion_pipeline as ingestion_pipeline_module
from app.document_processing.ingestion_pipeline import run_ingestion
from app.document_processing.loaders.base import LoaderParsingError
from app.repositories.document_repo import DocumentRepository


class FakeLoader:
    def load(self, path):
        return [Document(page_content="Contenido de prueba, suficientemente largo para trocear en chunks.")]


class FailingLoader:
    def load(self, path):
        raise LoaderParsingError("docx", "fichero corrupto de prueba")


class FakeVectorStore:
    def __init__(self):
        self.added = []

    def add_chunks(self, document_id, chunks):
        self.added.append((document_id, chunks))


def _create_temp_document(tmp_path, filename="informe.pdf"):
    document_repo = DocumentRepository()
    document = document_repo.create(filename=filename, format="pdf")
    tmp_file = tmp_path / filename
    tmp_file.write_bytes(b"contenido de prueba")
    return document, str(tmp_file)


def test_run_ingestion_success_transitions_to_done(tmp_path, monkeypatch):
    monkeypatch.setattr(ingestion_pipeline_module, "get_loader", lambda filename: FakeLoader())
    monkeypatch.setattr(ingestion_pipeline_module, "VectorStoreRepository", FakeVectorStore)

    document, path = _create_temp_document(tmp_path)

    run_ingestion(document.id, path, document.filename)

    updated = DocumentRepository().get(document.id)
    assert updated.status == "done"
    assert updated.chunk_count >= 1
    assert updated.error_message is None


def test_run_ingestion_parsing_error_transitions_to_error(tmp_path, monkeypatch):
    monkeypatch.setattr(ingestion_pipeline_module, "get_loader", lambda filename: FailingLoader())

    document, path = _create_temp_document(tmp_path, filename="informe.docx")

    run_ingestion(document.id, path, document.filename)

    updated = DocumentRepository().get(document.id)
    assert updated.status == "error"
    assert "fichero corrupto de prueba" in updated.error_message


def test_run_ingestion_retries_transient_embedding_failure_then_succeeds(tmp_path, monkeypatch):
    monkeypatch.setattr(ingestion_pipeline_module, "get_loader", lambda filename: FakeLoader())
    monkeypatch.setattr(ingestion_pipeline_module, "time", type("T", (), {"sleep": staticmethod(lambda s: None)}))

    attempts = {"count": 0}

    class FlakyVectorStore:
        def add_chunks(self, document_id, chunks):
            attempts["count"] += 1
            if attempts["count"] < 2:
                raise ConnectionError("fallo transitorio simulado")

    monkeypatch.setattr(ingestion_pipeline_module, "VectorStoreRepository", FlakyVectorStore)

    document, path = _create_temp_document(tmp_path)

    run_ingestion(document.id, path, document.filename)

    updated = DocumentRepository().get(document.id)
    assert updated.status == "done"
    assert attempts["count"] == 2


def test_run_ingestion_exhausts_retries_transitions_to_error(tmp_path, monkeypatch):
    monkeypatch.setattr(ingestion_pipeline_module, "get_loader", lambda filename: FakeLoader())
    monkeypatch.setattr(ingestion_pipeline_module, "time", type("T", (), {"sleep": staticmethod(lambda s: None)}))

    class AlwaysFailingVectorStore:
        def add_chunks(self, document_id, chunks):
            raise ConnectionError("fallo persistente simulado")

    monkeypatch.setattr(ingestion_pipeline_module, "VectorStoreRepository", AlwaysFailingVectorStore)

    document, path = _create_temp_document(tmp_path)

    run_ingestion(document.id, path, document.filename)

    updated = DocumentRepository().get(document.id)
    assert updated.status == "error"
