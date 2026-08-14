from pathlib import Path

from .loaders.base import DocumentLoader
from .loaders.pdf_loader import PDFLoader


class UnsupportedFormatError(Exception):
    def __init__(self, extension: str):
        self.extension = extension
        self.supported = sorted(_LOADERS)
        super().__init__(
            f"Formato '{extension}' no soportado. Formatos soportados: {self.supported}"
        )


_LOADERS: dict[str, type[DocumentLoader]] = {
    ".pdf": PDFLoader,
}


def get_loader(filename: str) -> DocumentLoader:
    extension = Path(filename).suffix.lower()
    loader_cls = _LOADERS.get(extension)
    if loader_cls is None:
        raise UnsupportedFormatError(extension)
    return loader_cls()
