from fastapi import APIRouter, HTTPException

from app.models.schemas import MessageResponse, SessionResponse
from app.repositories.chat_repo import ChatSessionRepository

router = APIRouter()


@router.post("/sessions", response_model=SessionResponse)
async def create_session() -> SessionResponse:
    chat_repo = ChatSessionRepository()
    session = chat_repo.create_session()
    return SessionResponse(
        id=session.id, title=session.title, created_at=session.created_at, updated_at=session.updated_at
    )


@router.get("/sessions", response_model=list[SessionResponse])
async def list_sessions() -> list[SessionResponse]:
    chat_repo = ChatSessionRepository()
    return [
        SessionResponse(id=s.id, title=s.title, created_at=s.created_at, updated_at=s.updated_at)
        for s in chat_repo.list_sessions()
    ]


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str) -> SessionResponse:
    chat_repo = ChatSessionRepository()
    session = chat_repo.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    return SessionResponse(
        id=session.id, title=session.title, created_at=session.created_at, updated_at=session.updated_at
    )


@router.get("/sessions/{session_id}/messages", response_model=list[MessageResponse])
async def get_session_messages(session_id: str) -> list[MessageResponse]:
    chat_repo = ChatSessionRepository()
    if chat_repo.get_session(session_id) is None:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    return [
        MessageResponse(
            id=m.id,
            role=m.role,
            content=m.content,
            created_at=m.created_at,
            model_used=m.model_used,
            sources=m.sources,
        )
        for m in chat_repo.list_messages(session_id)
    ]


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(session_id: str) -> None:
    chat_repo = ChatSessionRepository()
    if not chat_repo.delete_session(session_id):
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
