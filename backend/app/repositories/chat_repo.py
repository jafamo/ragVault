from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.models.entities import ChatMessage, ChatSession
from app.repositories.document_repo import _SessionLocal


class ChatSessionRepository:
    """Igual que DocumentRepository: una sesión de corta duración por
    método. Sesión y mensaje se gestionan desde el mismo repositorio
    porque son un agregado 1:N sin sentido independiente."""

    def __init__(self, session_factory: sessionmaker[Session] = _SessionLocal) -> None:
        self._session_factory = session_factory

    def create_session(self) -> ChatSession:
        with self._session_factory() as session:
            chat_session = ChatSession()
            session.add(chat_session)
            session.commit()
            session.refresh(chat_session)
            session.expunge(chat_session)
            return chat_session

    def list_sessions(self) -> list[ChatSession]:
        with self._session_factory() as session:
            sessions = list(
                session.scalars(select(ChatSession).order_by(ChatSession.updated_at.desc()))
            )
            session.expunge_all()
            return sessions

    def get_session(self, session_id: str) -> ChatSession | None:
        with self._session_factory() as session:
            chat_session = session.get(ChatSession, session_id)
            if chat_session is not None:
                session.expunge(chat_session)
            return chat_session

    def delete_session(self, session_id: str) -> bool:
        with self._session_factory() as session:
            chat_session = session.get(ChatSession, session_id)
            if chat_session is None:
                return False
            session.delete(chat_session)
            session.commit()
            return True

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        model_used: str | None = None,
        sources: str | None = None,
    ) -> ChatMessage | None:
        with self._session_factory() as session:
            chat_session = session.get(ChatSession, session_id)
            if chat_session is None:
                return None
            message = ChatMessage(
                session_id=session_id,
                role=role,
                content=content,
                model_used=model_used,
                sources=sources,
            )
            session.add(message)
            chat_session.updated_at = datetime.now(UTC)
            session.commit()
            session.refresh(message)
            session.expunge(message)
            return message

    def list_messages(self, session_id: str) -> list[ChatMessage]:
        with self._session_factory() as session:
            messages = list(
                session.scalars(
                    select(ChatMessage)
                    .where(ChatMessage.session_id == session_id)
                    .order_by(ChatMessage.created_at)
                )
            )
            session.expunge_all()
            return messages

    def set_title_if_empty(self, session_id: str, title: str) -> None:
        with self._session_factory() as session:
            chat_session = session.get(ChatSession, session_id)
            if chat_session is None or chat_session.title is not None:
                return
            chat_session.title = title
            session.commit()
