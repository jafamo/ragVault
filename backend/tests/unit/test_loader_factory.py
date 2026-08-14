import pytest

from app.document_processing.loader_factory import UnsupportedFormatError, get_loader
from app.document_processing.loaders.csv_loader import CSVLoader
from app.document_processing.loaders.docx_loader import DocxLoader
from app.document_processing.loaders.excel_loader import ExcelLoader
from app.document_processing.loaders.ods_loader import OdsLoader
from app.document_processing.loaders.odt_loader import OdtLoader
from app.document_processing.loaders.pdf_loader import PDFLoader
from app.document_processing.loaders.ppt_legacy_loader import PptLegacyLoader
from app.document_processing.loaders.pptx_loader import PptxLoader
from app.document_processing.loaders.text_loader import TextLoader


@pytest.mark.parametrize(
    ("filename", "expected_cls"),
    [
        ("informe.pdf", PDFLoader),
        ("informe.docx", DocxLoader),
        ("informe.odt", OdtLoader),
        ("informe.xlsx", ExcelLoader),
        ("informe.ods", OdsLoader),
        ("informe.csv", CSVLoader),
        ("informe.md", TextLoader),
        ("informe.txt", TextLoader),
        ("informe.pptx", PptxLoader),
        ("informe.ppt", PptLegacyLoader),
    ],
)
def test_extension_returns_expected_loader(filename, expected_cls):
    assert isinstance(get_loader(filename), expected_cls)


def test_unsupported_extension_raises():
    with pytest.raises(UnsupportedFormatError) as exc_info:
        get_loader("informe.rtf")

    supported = exc_info.value.supported
    assert supported == sorted(
        [".pdf", ".docx", ".odt", ".xlsx", ".ods", ".csv", ".md", ".txt", ".pptx", ".ppt"]
    )
