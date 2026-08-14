from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document

from .base import DocumentLoader


class PDFLoader(DocumentLoader):
    def load(self, path: str) -> list[Document]:
        return PyPDFLoader(path).load()
