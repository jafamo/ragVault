from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.config import settings
from app.core.embeddings import get_embeddings


class VectorStoreRepository:
    def __init__(self) -> None:
        self._store = Chroma(
            collection_name="ragvault",
            embedding_function=get_embeddings(),
            persist_directory=settings.chroma_persist_dir,
        )

    def add_chunks(self, document_id: str, chunks: list[Document]) -> None:
        for chunk in chunks:
            chunk.metadata["document_id"] = document_id
        self._store.add_documents(chunks)

    def similarity_search(self, query: str, k: int) -> list[tuple[Document, float]]:
        return self._store.similarity_search_with_relevance_scores(query, k=k)

    def delete_by_document_id(self, document_id: str) -> None:
        self._store.delete(where={"document_id": document_id})
