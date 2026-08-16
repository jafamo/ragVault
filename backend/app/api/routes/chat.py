import json
from collections.abc import AsyncIterator

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from starlette.concurrency import run_in_threadpool

from app.config import settings
from app.core.llm_provider import get_llm
from app.core.logging import get_logger
from app.core.rag_pipeline import (
    NO_DOCUMENTS_ANSWER,
    generate_title,
    make_generate_step_stream,
    retrieve_and_build_prompt,
    sources_from_context,
)
from app.models.schemas import ChatRequest, ModelsResponse
from app.repositories.chat_repo import ChatSessionRepository
from app.repositories.vector_store import VectorStoreRepository

router = APIRouter()
logger = get_logger(__name__)


def _normalize_model_name(name: str) -> str:
    """Ollama trata un nombre sin tag como su ':latest' implícito, p. ej.
    "nomic-embed-text" y "nomic-embed-text:latest" son el mismo modelo."""
    return name if ":" in name else f"{name}:latest"


def _sse(event: str, data: object) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def _try_generate_title(
    chat_repo: ChatSessionRepository, session_id: str, model: str, first_message: str
) -> None:
    try:
        # generate_title hace una llamada bloqueante (llm.invoke); se
        # offloadea a un thread para no congelar el event loop mientras
        # dura la petición a Ollama, cosa que aquí es más grave que en el
        # endpoint no-streaming de antes: con el StreamingResponse ya
        # abierto, bloquear el loop también impide que se entreguen al
        # cliente los frames SSE ya emitidos (p. ej. `done`) y bloquea el
        # resto de peticiones concurrentes al servidor.
        title = await run_in_threadpool(generate_title, get_llm(model), first_message)
        chat_repo.set_title_if_empty(session_id, title)
    except Exception:
        logger.warning("session_title_generation_failed", session_id=session_id)


def _stream_chat_response(
    request: Request,
    chat_repo: ChatSessionRepository,
    session_id: str,
    session_title: str | None,
    first_message: str,
    ctx: dict,
    model: str,
) -> AsyncIterator[str]:
    async def event_stream() -> AsyncIterator[str]:
        answer_parts: list[str] = []
        try:
            if not ctx["retrieved"]:
                answer_parts.append(NO_DOCUMENTS_ANSWER)
                yield _sse("chunk", NO_DOCUMENTS_ANSWER)
            else:
                async for piece in make_generate_step_stream(get_llm(model))(ctx):
                    if await request.is_disconnected():
                        return
                    answer_parts.append(piece)
                    yield _sse("chunk", piece)
        except Exception:
            logger.warning("chat_generation_failed", session_id=session_id)
            yield _sse("error", {"message": "Ha fallado la generación de la respuesta."})
            return

        if await request.is_disconnected():
            return

        answer = "".join(answer_parts)
        sources = sources_from_context(ctx)
        sources_json = json.dumps(
            {
                "chunks_used": sources,
                "retriever_config": {"top_k": settings.retrieval_top_k, "filter_tags": []},
            }
        )
        chat_repo.add_message(
            session_id, role="assistant", content=answer, model_used=model, sources=sources_json
        )

        logger.info(
            "chat_answered", sources_count=len(sources), model=model, session_id=session_id
        )
        yield _sse("done", {"sources": sources, "model": model})

        if session_title is None:
            await _try_generate_title(chat_repo, session_id, model, first_message)

    return event_stream()


@router.post("/chat")
async def chat(request: ChatRequest, http_request: Request) -> StreamingResponse:
    chat_repo = ChatSessionRepository()
    session = chat_repo.get_session(request.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    model = request.model or settings.ollama_model
    chat_repo.add_message(request.session_id, role="user", content=request.message)

    try:
        ctx = retrieve_and_build_prompt(
            question=request.message,
            vector_store=VectorStoreRepository(),
            top_k=settings.retrieval_top_k,
        )
    except Exception as exc:
        logger.warning("chat_retrieval_failed", session_id=request.session_id)
        raise HTTPException(status_code=503, detail="Fallo al recuperar documentos") from exc

    return StreamingResponse(
        _stream_chat_response(
            http_request, chat_repo, request.session_id, session.title, request.message, ctx, model
        ),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


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
