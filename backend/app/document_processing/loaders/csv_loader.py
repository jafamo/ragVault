import csv

from langchain_community.document_loaders.csv_loader import (
    CSVLoader as LangchainCSVLoader,
)
from langchain_core.documents import Document

from .base import DocumentLoader, LoaderParsingError


class CSVLoader(DocumentLoader):
    def load(self, path: str) -> list[Document]:
        try:
            return LangchainCSVLoader(path, autodetect_encoding=True).load()
        except (csv.Error, UnicodeDecodeError) as exc:
            raise LoaderParsingError("csv", "el fichero CSV está malformado") from exc
