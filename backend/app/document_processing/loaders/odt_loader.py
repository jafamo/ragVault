import zipfile
from xml.parsers.expat import ExpatError

from langchain_core.documents import Document
from odf.opendocument import load
from odf.table import Table, TableRow
from odf.teletype import extractText
from odf.text import H, P

from .base import DocumentLoader, LoaderParsingError


def _is_within_table(node) -> bool:
    parent = node.parentNode
    while parent is not None:
        if getattr(parent, "qname", (None, None))[1] == "table":
            return True
        parent = parent.parentNode
    return False


def _table_to_text(table: Table) -> str:
    rows = []
    for row in table.getElementsByType(TableRow):
        cells = [extractText(cell) for cell in row.childNodes]
        rows.append(" | ".join(cells))
    return "\n".join(rows)


class OdtLoader(DocumentLoader):
    def load(self, path: str) -> list[Document]:
        try:
            document = load(path)
        except (zipfile.BadZipFile, ExpatError) as exc:
            raise LoaderParsingError("odt", "el fichero está corrupto o no es un ODT válido") from exc

        paragraphs = [
            extractText(p)
            for p in document.getElementsByType(P) + document.getElementsByType(H)
            if not _is_within_table(p)
        ]
        tables = [_table_to_text(table) for table in document.getElementsByType(Table)]

        parts = [p for p in paragraphs if p.strip()] + [t for t in tables if t.strip()]
        return [Document(page_content="\n\n".join(parts))]
