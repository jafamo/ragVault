import asyncio
import mimetypes
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile
from fastapi.responses import FileResponse
from starlette import status

from app.config import settings
from app.core.cancellation import cancellation_registry
from app.core.logging import get_logger
from app.core.progress import progress_tracker
from app.document_processing.ingestion_pipeline import run_ingestion
from app.document_processing.loader_factory import UnsupportedFormatError, get_loader
from app.models.schemas import (
    DocumentListItem,
    DocumentListResponse,
    DocumentResponse,
    DocumentStatusResponse,
    TagAssignRequest,
    TagListResponse,
)
from app.repositories.document_repo import DocumentRepository
from app.repositories.tag_repo import TagRepository
from app.repositories.vector_store import VectorStoreRepository

router = APIRouter()
logger = get_logger(__name__)

_CANCEL_WAIT_TIMEOUT_SECONDS = 5
_CANCEL_WAIT_POLL_SECONDS = 0.1


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(file: UploadFile, background_tasks: BackgroundTasks) -> DocumentResponse:
    filename = file.filename or "documento"
    extension = Path(filename).suffix.lower()

    try:
        get_loader(filename)
    except UnsupportedFormatError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc

    document_id = str(uuid4())
    uploads_dir = Path(settings.uploads_dir)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    dest_path = uploads_dir / f"{document_id}{extension}"
    dest_path.write_bytes(await file.read())
    absolute_path = str(dest_path.resolve())
    size_bytes = dest_path.stat().st_size

    document_repo = DocumentRepository()
    document = document_repo.create(
        document_id=document_id,
        filename=filename,
        format=extension.lstrip("."),
        size_bytes=size_bytes,
        absolute_path=absolute_path,
    )

    background_tasks.add_task(run_ingestion, document.id, absolute_path, filename)

    logger.info("document_queued", filename=filename, document_id=document.id)

    return DocumentResponse(
        id=document.id,
        filename=document.filename,
        format=document.format,
        chunk_count=document.chunk_count,
        uploaded_at=document.uploaded_at,
        status=document.status,
    )


@router.get("/documents/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(document_id: str) -> DocumentStatusResponse:
    document_repo = DocumentRepository()
    document = document_repo.get(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    progress = progress_tracker.get(document_id)

    return DocumentStatusResponse(
        status=document.status,
        stage=progress.stage if progress else None,
        percent=progress.percent if progress else None,
        error_message=document.error_message,
        chunk_count=document.chunk_count,
    )

@router.post("/documents/{document_id}/tags", response_model=TagListResponse)
async def assign_document_tags(document_id: str, payload: TagAssignRequest) -> TagListResponse:
    tag_repo = TagRepository()
    tags = tag_repo.assign(document_id, payload.tags)
    if tags is None:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    logger.info("document_tags_assigned", document_id=document_id, tags=tags)

    return TagListResponse(tags=tags)

@router.get("/documents/{document_id}/tags", response_model=TagListResponse)
async def get_document_tags(document_id: str) -> TagListResponse:
    tag_repo = TagRepository()
    tags = tag_repo.list_for_document(document_id)
    if tags is None:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    return TagListResponse(tags=tags)


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents() -> DocumentListResponse:
    document_repo = DocumentRepository()
    documents = document_repo.list_all()

    return DocumentListResponse(
        documents=[
            DocumentListItem(
                id=document.id,
                status=document.status,
                filename=document.filename,
                format=document.format,
                size_bytes=document.size_bytes,
                tags=[tag.name for tag in document.tags],
                absolute_path=document.absolute_path,
                uploaded_at=document.uploaded_at,
            )
            for document in documents
        ]
    )


@router.get("/documents/{document_id}/file")
async def get_document_file(document_id: str) -> FileResponse:
    document_repo = DocumentRepository()
    document = document_repo.get(document_id)
    if document is None or not document.absolute_path:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    file_path = Path(document.absolute_path)
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="El fichero ya no está disponible en disco")

    media_type = mimetypes.guess_type(document.filename)[0] or "application/octet-stream"
    return FileResponse(
        file_path,
        media_type=media_type,
        filename=document.filename,
        content_disposition_type="inline",
    )


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: str) -> None:
    document_repo = DocumentRepository()
    document = document_repo.get(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    if document.status == "processing":
        cancellation_registry.request_cancel(document_id)
        waited = 0.0
        while waited < _CANCEL_WAIT_TIMEOUT_SECONDS:
            current = document_repo.get(document_id)
            if current is None or current.status != "processing":
                break
            await asyncio.sleep(_CANCEL_WAIT_POLL_SECONDS)
            waited += _CANCEL_WAIT_POLL_SECONDS
        logger.info("document_ingestion_cancel_requested", document_id=document_id, waited_seconds=waited)

    vector_store = VectorStoreRepository()
    vector_store.delete_by_document_id(document_id)

    if document.absolute_path:
        Path(document.absolute_path).unlink(missing_ok=True)

    document_repo.delete(document_id)
    logger.info("document_deleted", document_id=document_id)
