from pathlib import Path

from .loaders.base import DocumentLoader
from .loaders.csv_loader import CSVLoader
from .loaders.docx_loader import DocxLoader
from .loaders.excel_loader import ExcelLoader
from .loaders.ods_loader import OdsLoader
from .loaders.odt_loader import OdtLoader
from .loaders.pdf_loader import PDFLoader
from .loaders.ppt_legacy_loader import PptLegacyLoader
from .loaders.pptx_loader import PptxLoader
from .loaders.text_loader import TextLoader


class UnsupportedFormatError(Exception):
    def __init__(self, extension: str):
        self.extension = extension
        self.supported = sorted(_LOADERS)
        super().__init__(
            f"Formato '{extension}' no soportado. Formatos soportados: {self.supported}"
        )


_LOADERS: dict[str, type[DocumentLoader]] = {
    ".pdf": PDFLoader,
    ".docx": DocxLoader,
    ".odt": OdtLoader,
    ".xlsx": ExcelLoader,
    ".ods": OdsLoader,
    ".csv": CSVLoader,
    ".md": TextLoader,
    ".txt": TextLoader,
    ".pptx": PptxLoader,
    ".ppt": PptLegacyLoader,
}


def get_loader(filename: str) -> DocumentLoader:
    extension = Path(filename).suffix.lower()
    loader_cls = _LOADERS.get(extension)
    if loader_cls is None:
        raise UnsupportedFormatError(extension)
    return loader_cls()
