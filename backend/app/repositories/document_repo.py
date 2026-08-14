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
    def __init__(self, session: Session | None = None) -> None:
        self._session = session or _SessionLocal()

    def create(self, filename: str, format: str, chunk_count: int) -> Document:
        document = Document(filename=filename, format=format, chunk_count=chunk_count)
        self._session.add(document)
        self._session.commit()
        self._session.refresh(document)
        return document

    def get(self, document_id: str) -> Document | None:
        return self._session.get(Document, document_id)

    def list(self) -> list[Document]:
        return list(self._session.scalars(select(Document)))
