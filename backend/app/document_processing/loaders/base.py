from abc import ABC, abstractmethod

from langchain_core.documents import Document


class DocumentLoader(ABC):
    @abstractmethod
    def load(self, path: str) -> list[Document]:
        """Carga un fichero y lo devuelve como documentos de LangChain."""
