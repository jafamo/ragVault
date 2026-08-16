import io

from langchain_core.documents import Document

import app.api.routes.documents as documents_module
import app.document_processing.ingestion_pipeline as ingestion_pipeline_module
from app.core.cancellation import cancellation_registry
from app.repositories.document_repo import DocumentRepository


class FakeLoader:
    def load(self, path):
        return [Document(page_content="Contenido de prueba, suficientemente largo para trocear.")]


class FakeVectorStore:
    def __init__(self):
        self.deleted_document_ids = []

    def add_chunks(self, document_id, chunks):
        pass

    def delete_by_document_id(self, document_id):
        self.deleted_document_ids.append(document_id)


def _upload(client, monkeypatch, tmp_path, fake_store):
    monkeypatch.setattr(documents_module.settings, "uploads_dir", str(tmp_path))
    monkeypatch.setattr(documents_module, "get_loader", lambda filename: FakeLoader())
    monkeypatch.setattr(ingestion_pipeline_module, "get_loader", lambda filename: FakeLoader())
    monkeypatch.setattr(ingestion_pipeline_module, "VectorStoreRepository", lambda: fake_store)
    monkeypatch.setattr(documents_module, "VectorStoreRepository", lambda: fake_store)

    response = client.post(
        "/upload",
        files={"file": ("informe.pdf", io.BytesIO(b"%PDF-1.4 fake"), "application/pdf")},
    )
    assert response.status_code == 202
    return response.json()


def test_list_documents_includes_size_and_absolute_path(client, monkeypatch, tmp_path):
    fake_store = FakeVectorStore()
    body = _upload(client, monkeypatch, tmp_path, fake_store)

    response = client.get("/documents")
    assert response.status_code == 200

    entries = response.json()["documents"]
    entry = next(item for item in entries if item["id"] == body["id"])
    assert entry["status"] == "done"
    assert entry["filename"] == "informe.pdf"
    assert entry["format"] == "pdf"
    assert entry["size_bytes"] > 0
    assert entry["absolute_path"].endswith(f"{body['id']}.pdf")
    assert entry["tags"] == []


def test_delete_document_removes_it_and_its_chunks_and_file(client, monkeypatch, tmp_path):
    fake_store = FakeVectorStore()
    body = _upload(client, monkeypatch, tmp_path, fake_store)

    list_response = client.get("/documents")
    entry = next(item for item in list_response.json()["documents"] if item["id"] == body["id"])
    absolute_path = entry["absolute_path"]
    from pathlib import Path

    assert Path(absolute_path).exists()

    delete_response = client.delete(f"/documents/{body['id']}")
    assert delete_response.status_code == 204
    assert body["id"] in fake_store.deleted_document_ids
    assert not Path(absolute_path).exists()

    list_response = client.get("/documents")
    assert all(item["id"] != body["id"] for item in list_response.json()["documents"])


def test_delete_nonexistent_document_returns_404(client):
    response = client.delete("/documents/does-not-exist")
    assert response.status_code == 404


def test_get_document_file_returns_content(client, monkeypatch, tmp_path):
    fake_store = FakeVectorStore()
    body = _upload(client, monkeypatch, tmp_path, fake_store)

    response = client.get(f"/documents/{body['id']}/file")

    assert response.status_code == 200
    assert response.content == b"%PDF-1.4 fake"
    assert response.headers["content-type"] == "application/pdf"


def test_get_document_file_returns_404_when_absolute_path_missing(client):
    document_repo = DocumentRepository()
    document = document_repo.create(filename="sin-ruta.pdf", format="pdf")

    response = client.get(f"/documents/{document.id}/file")

    assert response.status_code == 404


def test_get_document_file_returns_404_when_file_deleted_from_disk(client, monkeypatch, tmp_path):
    fake_store = FakeVectorStore()
    body = _upload(client, monkeypatch, tmp_path, fake_store)

    entry = client.get("/documents").json()["documents"]
    absolute_path = next(item for item in entry if item["id"] == body["id"])["absolute_path"]
    from pathlib import Path

    Path(absolute_path).unlink()

    response = client.get(f"/documents/{body['id']}/file")
    assert response.status_code == 404


def test_get_document_file_returns_404_for_nonexistent_document(client):
    response = client.get("/documents/does-not-exist/file")
    assert response.status_code == 404


def test_delete_processing_document_requests_cancellation_then_deletes(client, monkeypatch):
    monkeypatch.setattr(documents_module, "_CANCEL_WAIT_TIMEOUT_SECONDS", 0.2)
    monkeypatch.setattr(documents_module, "_CANCEL_WAIT_POLL_SECONDS", 0.05)
    fake_store = FakeVectorStore()
    monkeypatch.setattr(documents_module, "VectorStoreRepository", lambda: fake_store)

    document_repo = DocumentRepository()
    document = document_repo.create(filename="largo.pdf", format="pdf")
    document_repo.update_status(document.id, "processing")

    delete_response = client.delete(f"/documents/{document.id}")

    assert delete_response.status_code == 204
    assert cancellation_registry.is_cancelled(document.id) is True
    assert document.id in fake_store.deleted_document_ids
    assert document_repo.get(document.id) is None
