import pytest

from app.document_processing.loader_factory import UnsupportedFormatError, get_loader
from app.document_processing.loaders.pdf_loader import PDFLoader


def test_pdf_extension_returns_pdf_loader():
    loader = get_loader("informe.pdf")
    assert isinstance(loader, PDFLoader)


def test_unsupported_extension_raises():
    with pytest.raises(UnsupportedFormatError):
        get_loader("informe.docx")
