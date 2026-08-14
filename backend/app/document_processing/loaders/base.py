from abc import ABC, abstractmethod

from langchain_core.documents import Document


class LoaderParsingError(Exception):
    def __init__(self, format: str, detail: str):
        self.format = format
        self.detail = detail
        super().__init__(f"Error al parsear fichero '{format}': {detail}")


class DocumentLoader(ABC):
    @abstractmethod
    def load(self, path: str) -> list[Document]:
        """Carga un fichero y lo devuelve como documentos de LangChain."""
