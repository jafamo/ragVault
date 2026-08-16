from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.orm import Session, selectinload, sessionmaker

from app.config import settings
from app.models.entities import Base, Document

Path(settings.sqlite_path).parent.mkdir(parents=True, exist_ok=True)
_engine = create_engine(f"sqlite:///{settings.sqlite_path}")
_SessionLocal = sessionmaker(bind=_engine)


def init_db() -> None:
    """`create_all` no altera tablas ya existentes, así que las columnas
    añadidas a `Document` tras el primer arranque (`size_bytes`,
    `absolute_path`) se rellenan aquí con un `ALTER TABLE` idempotente.
    El proyecto no tiene Alembic realmente configurado todavía pese a
    mencionarlo en el stack objetivo; esto es un ajuste equivalente hasta
    que exista ese setup."""
    Base.metadata.create_all(_engine)
    inspector = inspect(_engine)
    existing_columns = {col["name"] for col in inspector.get_columns("documents")}
    with _engine.begin() as connection:
        if "size_bytes" not in existing_columns:
            connection.execute(text("ALTER TABLE documents ADD COLUMN size_bytes INTEGER"))
        if "absolute_path" not in existing_columns:
            connection.execute(text("ALTER TABLE documents ADD COLUMN absolute_path VARCHAR"))


class DocumentRepository:
    """Cada método abre y cierra su propia sesión de corta duración —
    evita agotar el connection pool cuando se instancia una vez por
    petición/tarea (patrón usado en toda la API), especialmente con el
    polling de GET /documents/{id}/status."""

    def __init__(self, session_factory: sessionmaker[Session] = _SessionLocal) -> None:
        self._session_factory = session_factory

    def create(
        self,
        filename: str,
        format: str,
        document_id: str | None = None,
        size_bytes: int | None = None,
        absolute_path: str | None = None,
    ) -> Document:
        with self._session_factory() as session:
            document = Document(
                id=document_id or str(uuid4()),
                filename=filename,
                format=format,
                status="queued",
                size_bytes=size_bytes,
                absolute_path=absolute_path,
            )
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

    def list_all(self) -> list[Document]:
        """Igual que `list()` pero precarga `tags` para poder leerlos tras
        cerrar la sesión (necesario para el listado de la biblioteca)."""
        with self._session_factory() as session:
            documents = list(
                session.scalars(select(Document).options(selectinload(Document.tags)))
            )
            session.expunge_all()
            return documents

    def delete(self, document_id: str) -> bool:
        with self._session_factory() as session:
            document = session.get(Document, document_id)
            if document is None:
                return False
            session.delete(document)
            session.commit()
            return True

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
