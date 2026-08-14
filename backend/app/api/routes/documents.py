import tempfile
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile
from starlette import status

from app.core.logging import get_logger
from app.core.progress import progress_tracker
from app.document_processing.ingestion_pipeline import run_ingestion
from app.document_processing.loader_factory import UnsupportedFormatError, get_loader
from app.models.schemas import (
    DocumentResponse,
    DocumentStatusResponse,
    TagAssignRequest,
    TagListResponse,
)
from app.repositories.document_repo import DocumentRepository
from app.repositories.tag_repo import TagRepository

router = APIRouter()
logger = get_logger(__name__)


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(file: UploadFile, background_tasks: BackgroundTasks) -> DocumentResponse:
    filename = file.filename or "documento"
    extension = Path(filename).suffix.lower()

    try:
        get_loader(filename)
    except UnsupportedFormatError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc

    with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    document_repo = DocumentRepository()
    document = document_repo.create(filename=filename, format=extension.lstrip("."))

    background_tasks.add_task(run_ingestion, document.id, tmp_path, filename)

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
