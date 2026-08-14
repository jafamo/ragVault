from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from app.models.entities import Document, Tag, document_tags
from app.repositories.document_repo import _SessionLocal

KNOWN_STATUSES = ["queued", "processing", "done", "error"]
TIMELINE_WINDOWS_DAYS = [5, 15, 30, 90, 365]


class StatsRepository:
    """Consultas de solo lectura para el dashboard de estadísticas —
    separado de DocumentRepository porque agrega datos con un propósito
    distinto (reporting) al CRUD del ciclo de vida de un documento."""

    def __init__(self, session_factory: sessionmaker[Session] = _SessionLocal) -> None:
        self._session_factory = session_factory

    def by_format(self) -> dict[str, int]:
        with self._session_factory() as session:
            rows = session.execute(
                select(Document.format, func.count()).group_by(Document.format)
            ).all()
            return {row[0]: row[1] for row in rows}

    def by_status(self) -> dict[str, int]:
        with self._session_factory() as session:
            rows = session.execute(
                select(Document.status, func.count()).group_by(Document.status)
            ).all()
            counts = {status: 0 for status in KNOWN_STATUSES}
            counts.update({row[0]: row[1] for row in rows})
            return counts

    def errors(self) -> list[Document]:
        with self._session_factory() as session:
            documents = list(
                session.scalars(select(Document).where(Document.status == "error"))
            )
            session.expunge_all()
            return documents

    def timeline(self, now: datetime | None = None) -> dict[int, int]:
        reference = now or datetime.now(UTC)
        with self._session_factory() as session:
            return {
                days: session.scalar(
                    select(func.count()).where(
                        Document.uploaded_at >= reference - timedelta(days=days)
                    )
                )
                or 0
                for days in TIMELINE_WINDOWS_DAYS
            }

    def by_tag(self) -> dict[str, int]:
        with self._session_factory() as session:
            tag_rows = session.execute(
                select(Tag.name, func.count(document_tags.c.document_id))
                .join(document_tags, document_tags.c.tag_id == Tag.id)
                .group_by(Tag.name)
            ).all()
            untagged = session.scalar(
                select(func.count())
                .select_from(Document)
                .where(Document.id.not_in(select(document_tags.c.document_id)))
            )
            counts = {row[0]: row[1] for row in tag_rows}
            counts["sin_tag"] = untagged or 0
            return counts
