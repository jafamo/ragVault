import io

from langchain_core.documents import Document

import app.api.routes.documents as documents_module
import app.document_processing.ingestion_pipeline as ingestion_pipeline_module


class FakeLoader:
    def load(self, path):
        return [Document(page_content="Contenido de prueba del PDF.")]


class FakeVectorStore:
    def __init__(self):
        self.added = []

    def add_chunks(self, document_id, chunks):
        self.added.append((document_id, chunks))


def test_upload_pdf_returns_202_queued_then_status_done(client, monkeypatch):
    monkeypatch.setattr(documents_module, "get_loader", lambda filename: FakeLoader())
    monkeypatch.setattr(ingestion_pipeline_module, "get_loader", lambda filename: FakeLoader())
    monkeypatch.setattr(ingestion_pipeline_module, "VectorStoreRepository", FakeVectorStore)

    response = client.post(
        "/upload",
        files={"file": ("informe.pdf", io.BytesIO(b"%PDF-1.4 fake"), "application/pdf")},
    )

    assert response.status_code == 202
    body = response.json()
    assert body["filename"] == "informe.pdf"
    assert body["format"] == "pdf"
    assert body["status"] == "queued"

    status_response = client.get(f"/documents/{body['id']}/status")
    assert status_response.status_code == 200
    status_body = status_response.json()
    assert status_body["status"] == "done"
    assert status_body["chunk_count"] >= 1


def test_upload_unsupported_format_returns_415(client):
    response = client.post(
        "/upload",
        files={"file": ("informe.rtf", io.BytesIO(b"contenido"), "application/octet-stream")},
    )

    assert response.status_code == 415
