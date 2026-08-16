import json

import httpx
from fastapi import APIRouter, HTTPException

from app.config import settings
from app.core.llm_provider import get_llm
from app.core.logging import get_logger
from app.core.rag_pipeline import generate_title, run_pipeline
from app.models.schemas import ChatRequest, ChatResponse, ModelsResponse
from app.repositories.chat_repo import ChatSessionRepository
from app.repositories.vector_store import VectorStoreRepository

router = APIRouter()
logger = get_logger(__name__)


def _normalize_model_name(name: str) -> str:
    """Ollama trata un nombre sin tag como su ':latest' implícito, p. ej.
    "nomic-embed-text" y "nomic-embed-text:latest" son el mismo modelo."""
    return name if ":" in name else f"{name}:latest"


def _try_generate_title(
    chat_repo: ChatSessionRepository, session_id: str, model: str, first_message: str
) -> None:
    try:
        title = generate_title(get_llm(model), first_message)
        chat_repo.set_title_if_empty(session_id, title)
    except Exception:
        logger.warning("session_title_generation_failed", session_id=session_id)


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    chat_repo = ChatSessionRepository()
    session = chat_repo.get_session(request.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    model = request.model or settings.ollama_model
    chat_repo.add_message(request.session_id, role="user", content=request.message)

    answer, sources = run_pipeline(
        question=request.message,
        vector_store=VectorStoreRepository(),
        llm=get_llm(model),
        top_k=settings.retrieval_top_k,
    )

    sources_json = json.dumps(
        {
            "chunks_used": sources,
            "retriever_config": {"top_k": settings.retrieval_top_k, "filter_tags": []},
        }
    )
    chat_repo.add_message(
        request.session_id, role="assistant", content=answer, model_used=model, sources=sources_json
    )

    if session.title is None:
        _try_generate_title(chat_repo, request.session_id, model, request.message)

    logger.info(
        "chat_answered", sources_count=len(sources), model=model, session_id=request.session_id
    )
    return ChatResponse(answer=answer, sources=sources, model=model)


@router.get("/models", response_model=ModelsResponse)
async def list_models() -> ModelsResponse:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.ollama_base_url}/api/tags")
            resp.raise_for_status()
    except httpx.HTTPError as exc:
        logger.warning("ollama_models_unreachable", ollama_base_url=settings.ollama_base_url)
        raise HTTPException(status_code=503, detail="Ollama no disponible") from exc

    names = [m["name"] for m in resp.json().get("models", [])]
    embed_model = _normalize_model_name(settings.ollama_embed_model)
    models = [name for name in names if _normalize_model_name(name) != embed_model]

    return ModelsResponse(models=models, default=settings.ollama_model)
