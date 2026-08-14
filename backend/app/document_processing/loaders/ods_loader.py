import zipfile
from xml.parsers.expat import ExpatError

from langchain_core.documents import Document
from odf.opendocument import load
from odf.table import Table, TableCell, TableRow
from odf.teletype import extractText

from .base import DocumentLoader, LoaderParsingError


class OdsLoader(DocumentLoader):
    def load(self, path: str) -> list[Document]:
        try:
            document = load(path)
        except (zipfile.BadZipFile, ExpatError) as exc:
            raise LoaderParsingError("ods", "el fichero está corrupto o no es un ODS válido") from exc

        documents = []
        for sheet in document.getElementsByType(Table):
            rows = []
            for row in sheet.getElementsByType(TableRow):
                cells = [extractText(cell) for cell in row.getElementsByType(TableCell)]
                rows.append(" | ".join(cells))
            text = "\n".join(row for row in rows if row.strip(" |"))
            if text.strip():
                sheet_name = sheet.getAttribute("name") or "hoja"
                documents.append(Document(page_content=text, metadata={"sheet_name": sheet_name}))
        return documents
