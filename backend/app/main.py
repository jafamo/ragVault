import uuid
from contextlib import asynccontextmanager

import httpx
import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.chat import router as chat_router
from app.api.routes.documents import router as documents_router
from app.config import settings
from app.core.logging import configure_logging, get_logger
from app.repositories.document_repo import init_db

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="RagVault", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents_router)
app.include_router(chat_router)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)
    try:
        response = await call_next(request)
    finally:
        structlog.contextvars.clear_contextvars()
    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/health")
async def health() -> dict:
    ollama_status = "unreachable"
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(f"{settings.ollama_base_url}/api/tags")
            if resp.status_code == 200:
                ollama_status = "reachable"
    except httpx.HTTPError:
        logger.warning("ollama_health_check_failed", ollama_base_url=settings.ollama_base_url)

    return {"status": "ok", "ollama": ollama_status}


if __name__ == "__main__":
    import uvicorn

    from app.core.logging import UVICORN_LOG_CONFIG

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        log_config=UVICORN_LOG_CONFIG,
    )
