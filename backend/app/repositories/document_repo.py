from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.models.entities import Base, Document

Path(settings.sqlite_path).parent.mkdir(parents=True, exist_ok=True)
_engine = create_engine(f"sqlite:///{settings.sqlite_path}")
_SessionLocal = sessionmaker(bind=_engine)


def init_db() -> None:
    Base.metadata.create_all(_engine)


class DocumentRepository:
    """Cada método abre y cierra su propia sesión de corta duración —
    evita agotar el connection pool cuando se instancia una vez por
    petición/tarea (patrón usado en toda la API), especialmente con el
    polling de GET /documents/{id}/status."""

    def __init__(self, session_factory: sessionmaker[Session] = _SessionLocal) -> None:
        self._session_factory = session_factory

    def create(self, filename: str, format: str) -> Document:
        with self._session_factory() as session:
            document = Document(filename=filename, format=format, status="queued")
            session.add(document)
            session.commit()
            session.refresh(document)
            session.expunge(document)
            return document

    def get(self, document_id: str) -> Document | None:
        with self._session_factory() as session:
            document = session.get(Document, document_id)
            if document is not None:
                session.expunge(document)
            return document

    def list(self) -> list[Document]:
        with self._session_factory() as session:
            documents = list(session.scalars(select(Document)))
            session.expunge_all()
            return documents

    def update_status(
        self,
        document_id: str,
        status: str,
        chunk_count: int | None = None,
        error_message: str | None = None,
    ) -> Document | None:
        with self._session_factory() as session:
            document = session.get(Document, document_id)
            if document is None:
                return None
            document.status = status
            if chunk_count is not None:
                document.chunk_count = chunk_count
            document.error_message = error_message
            session.commit()
            session.refresh(document)
            session.expunge(document)
            return document
