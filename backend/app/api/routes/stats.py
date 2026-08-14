from fastapi import APIRouter

from app.models.schemas import ErrorDocumentResponse
from app.repositories.stats_repo import StatsRepository

router = APIRouter(prefix="/stats")

@router.get("/by-format", response_model=dict[str, int])
async def stats_by_format() -> dict[str, int]:
    return StatsRepository().by_format()

@router.get("/by-status", response_model=dict[str, int])
async def stats_by_status() -> dict[str, int]:
    return StatsRepository().by_status()

@router.get("/errors", response_model=list[ErrorDocumentResponse])
async def stats_errors() -> list[ErrorDocumentResponse]:
    documents = StatsRepository().errors()
    return [
        ErrorDocumentResponse(
            id=document.id,
            filename=document.filename,
            format=document.format,
            error_message=document.error_message,
        )
        for document in documents
    ]

@router.get("/timeline", response_model=dict[str, int])
async def stats_timeline() -> dict[str, int]:
    return {str(days): count for days, count in StatsRepository().timeline().items()}

@router.get("/by-tag", response_model=dict[str, int])
async def stats_by_tag() -> dict[str, int]:
    return StatsRepository().by_tag()
