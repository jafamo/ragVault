import io

from langchain_core.documents import Document

import app.api.routes.documents as documents_module


class FakeLoader:
    def load(self, path):
        return [Document(page_content="Contenido de prueba del PDF.")]


class FakeVectorStore:
    def __init__(self):
        self.added = []

    def add_chunks(self, document_id, chunks):
        self.added.append((document_id, chunks))


def test_upload_pdf_returns_document_metadata(client, monkeypatch):
    monkeypatch.setattr(documents_module, "get_loader", lambda filename: FakeLoader())
    monkeypatch.setattr(documents_module, "VectorStoreRepository", FakeVectorStore)

    response = client.post(
        "/upload",
        files={"file": ("informe.pdf", io.BytesIO(b"%PDF-1.4 fake"), "application/pdf")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["filename"] == "informe.pdf"
    assert body["format"] == "pdf"
    assert body["chunk_count"] >= 1


def test_upload_unsupported_format_returns_415(client):
    response = client.post(
        "/upload",
        files={"file": ("informe.docx", io.BytesIO(b"contenido"), "application/octet-stream")},
    )

    assert response.status_code == 415
