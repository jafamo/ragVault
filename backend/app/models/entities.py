from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


document_tags = Table(
    "document_tags",
    Base.metadata,
    Column("document_id", String, ForeignKey("documents.id"), primary_key=True),
    Column("tag_id", String, ForeignKey("tags.id"), primary_key=True),
)


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    filename: Mapped[str] = mapped_column(String)
    format: Mapped[str] = mapped_column(String)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String, default="queued")
    error_message: Mapped[str | None] = mapped_column(String, nullable=True, default=None)
    tags: Mapped[list["Tag"]] = relationship(secondary=document_tags, back_populates="documents")


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String, unique=True)
    documents: Mapped[list[Document]] = relationship(secondary=document_tags, back_populates="tags")
