from datetime import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: str
    filename: str
    format: str
    chunk_count: int
    uploaded_at: datetime
    status: str


class DocumentStatusResponse(BaseModel):
    status: str
    stage: str | None = None
    percent: int | None = None
    error_message: str | None = None
    chunk_count: int


class ChatRequest(BaseModel):
    message: str
    model: str | None = None


class SourceResponse(BaseModel):
    document_id: str
    document_name: str
    page: int | None
    chunk_text: str
    similarity_score: float


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceResponse]
    model: str


class ModelsResponse(BaseModel):
    models: list[str]
    default: str

class TagAssignRequest(BaseModel):
    tags: list[str]

class TagListResponse(BaseModel):
    tags: list[str]

class ErrorDocumentResponse(BaseModel):
    id: str
    filename: str
    format: str
    error_message: str | None
