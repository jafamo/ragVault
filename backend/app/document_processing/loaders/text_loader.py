from langchain_community.document_loaders import TextLoader as LangchainTextLoader
from langchain_core.documents import Document

from .base import DocumentLoader, LoaderParsingError


class TextLoader(DocumentLoader):
    def load(self, path: str) -> list[Document]:
        try:
            return LangchainTextLoader(path, autodetect_encoding=True).load()
        except UnicodeDecodeError as exc:
            raise LoaderParsingError("text", "no se pudo decodificar el fichero de texto") from exc
