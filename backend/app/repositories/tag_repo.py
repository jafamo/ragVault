from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from app.models.entities import Document, Tag
from app.repositories.document_repo import _SessionLocal


class TagRepository:
    """Igual que DocumentRepository: una sesión de corta duración por
    método."""

    def __init__(self, session_factory: sessionmaker[Session] = _SessionLocal) -> None:
        self._session_factory = session_factory

    def assign(self, document_id: str, names: list[str]) -> list[str] | None:
        """Asocia `names` al documento, creando los tags que no existan
        (comparación insensible a mayúsculas/minúsculas). Devuelve la
        lista de tags del documento tras la asignación, o None si el
        documento no existe."""
        with self._session_factory() as session:
            document = session.get(Document, document_id)
            if document is None:
                return None

            for name in names:
                clean_name = name.strip()
                if not clean_name:
                    continue
                tag = session.scalar(
                    select(Tag).where(func.lower(Tag.name) == clean_name.lower())
                )
                if tag is None:
                    tag = Tag(name=clean_name)
                    session.add(tag)
                if tag not in document.tags:
                    document.tags.append(tag)

            session.commit()
            return [tag.name for tag in document.tags]

    def list_for_document(self, document_id: str) -> list[str] | None:
        with self._session_factory() as session:
            document = session.get(Document, document_id)
            if document is None:
                return None
            return [tag.name for tag in document.tags]
