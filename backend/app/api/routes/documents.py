import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile

from app.core.logging import get_logger
from app.document_processing.loader_factory import UnsupportedFormatError, get_loader
from app.document_processing.splitter import split_documents
from app.models.schemas import DocumentResponse
from app.repositories.document_repo import DocumentRepository
from app.repositories.vector_store import VectorStoreRepository

router = APIRouter()
logger = get_logger(__name__)


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(file: UploadFile) -> DocumentResponse:
    filename = file.filename or "documento"
    extension = Path(filename).suffix.lower()

    try:
        loader = get_loader(filename)
    except UnsupportedFormatError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc

    with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        raw_documents = loader.load(tmp_path)
        for doc in raw_documents:
            doc.metadata["source"] = filename
        chunks = split_documents(raw_documents)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    document_repo = DocumentRepository()
    document = document_repo.create(
        filename=filename, format=extension.lstrip("."), chunk_count=len(chunks)
    )

    if chunks:
        vector_store = VectorStoreRepository()
        vector_store.add_chunks(document.id, chunks)

    logger.info("document_ingested", filename=filename, chunk_count=len(chunks))

    return DocumentResponse(
        id=document.id,
        filename=document.filename,
        format=document.format,
        chunk_count=document.chunk_count,
        uploaded_at=document.uploaded_at,
    )
