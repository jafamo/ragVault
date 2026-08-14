from datetime import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: str
    filename: str
    format: str
    chunk_count: int
    uploaded_at: datetime


class ChatRequest(BaseModel):
    message: str


class SourceResponse(BaseModel):
    document_id: str
    document_name: str
    page: int | None
    chunk_text: str
    similarity_score: float


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceResponse]
