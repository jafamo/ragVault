from fastapi import APIRouter

from app.config import settings
from app.core.llm_provider import get_llm
from app.core.logging import get_logger
from app.core.rag_pipeline import run_pipeline
from app.models.schemas import ChatRequest, ChatResponse
from app.repositories.vector_store import VectorStoreRepository

router = APIRouter()
logger = get_logger(__name__)


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    answer, sources = run_pipeline(
        question=request.message,
        vector_store=VectorStoreRepository(),
        llm=get_llm(),
        top_k=settings.retrieval_top_k,
    )
    logger.info("chat_answered", sources_count=len(sources))
    return ChatResponse(answer=answer, sources=sources)
