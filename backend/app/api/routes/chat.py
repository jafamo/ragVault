import httpx
from fastapi import APIRouter, HTTPException

from app.config import settings
from app.core.llm_provider import get_llm
from app.core.logging import get_logger
from app.core.rag_pipeline import run_pipeline
from app.models.schemas import ChatRequest, ChatResponse, ModelsResponse
from app.repositories.vector_store import VectorStoreRepository

router = APIRouter()
logger = get_logger(__name__)


def _normalize_model_name(name: str) -> str:
    """Ollama trata un nombre sin tag como su ':latest' implícito, p. ej.
    "nomic-embed-text" y "nomic-embed-text:latest" son el mismo modelo."""
    return name if ":" in name else f"{name}:latest"


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    model = request.model or settings.ollama_model
    answer, sources = run_pipeline(
        question=request.message,
        vector_store=VectorStoreRepository(),
        llm=get_llm(model),
        top_k=settings.retrieval_top_k,
    )
    logger.info("chat_answered", sources_count=len(sources), model=model)
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
