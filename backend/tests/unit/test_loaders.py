from pathlib import Path

import pytest

from app.document_processing.loaders.base import LoaderParsingError
from app.document_processing.loaders.csv_loader import CSVLoader
from app.document_processing.loaders.docx_loader import DocxLoader
from app.document_processing.loaders.excel_loader import ExcelLoader
from app.document_processing.loaders.ods_loader import OdsLoader
from app.document_processing.loaders.odt_loader import OdtLoader
from app.document_processing.loaders.pptx_loader import PptxLoader
from app.document_processing.loaders.text_loader import TextLoader

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def test_docx_loader_extracts_text():
    docs = DocxLoader().load(str(FIXTURES / "valid.docx"))
    text = "\n".join(doc.page_content for doc in docs)
    assert "Contenido de prueba del DOCX." in text


def test_docx_loader_extracts_embedded_table():
    docs = DocxLoader().load(str(FIXTURES / "valid.docx"))
    text = "\n".join(doc.page_content for doc in docs)
    assert "Producto | Precio" in text
    assert "Widget | 9.99" in text


def test_docx_loader_corrupt_file_raises():
    with pytest.raises(LoaderParsingError):
        DocxLoader().load(str(FIXTURES / "corrupt.docx"))


def test_odt_loader_extracts_text():
    docs = OdtLoader().load(str(FIXTURES / "valid.odt"))
    text = "\n".join(doc.page_content for doc in docs)
    assert "Contenido de prueba del ODT." in text


def test_odt_loader_extracts_embedded_table():
    docs = OdtLoader().load(str(FIXTURES / "valid.odt"))
    text = "\n".join(doc.page_content for doc in docs)
    assert "Producto | Precio" in text
    assert "Widget | 9.99" in text


def test_odt_loader_corrupt_file_raises():
    with pytest.raises(LoaderParsingError):
        OdtLoader().load(str(FIXTURES / "corrupt.odt"))


def test_excel_loader_extracts_sheet_text():
    docs = ExcelLoader().load(str(FIXTURES / "valid.xlsx"))
    assert len(docs) == 1
    assert docs[0].metadata["sheet_name"] == "Hoja1"
    assert "Widget" in docs[0].page_content


def test_excel_loader_corrupt_file_raises():
    with pytest.raises(LoaderParsingError):
        ExcelLoader().load(str(FIXTURES / "corrupt.xlsx"))


def test_ods_loader_extracts_sheet_text():
    docs = OdsLoader().load(str(FIXTURES / "valid.ods"))
    assert len(docs) == 1
    assert docs[0].metadata["sheet_name"] == "Hoja1"
    assert "Widget" in docs[0].page_content


def test_ods_loader_corrupt_file_raises():
    with pytest.raises(LoaderParsingError):
        OdsLoader().load(str(FIXTURES / "corrupt.ods"))


def test_pptx_loader_extracts_slide_text():
    docs = PptxLoader().load(str(FIXTURES / "valid.pptx"))
    assert len(docs) == 1
    assert docs[0].metadata["slide_number"] == 1
    assert "Contenido de prueba del PPTX." in docs[0].page_content


def test_pptx_loader_corrupt_file_raises():
    with pytest.raises(LoaderParsingError):
        PptxLoader().load(str(FIXTURES / "corrupt.pptx"))


def test_csv_loader_extracts_rows():
    docs = CSVLoader().load(str(FIXTURES / "valid.csv"))
    assert len(docs) == 1
    assert "Widget" in docs[0].page_content


def test_text_loader_extracts_md():
    docs = TextLoader().load(str(FIXTURES / "valid.md"))
    assert "Contenido de prueba del Markdown." in docs[0].page_content


def test_text_loader_extracts_txt():
    docs = TextLoader().load(str(FIXTURES / "valid.txt"))
    assert "Contenido de prueba del TXT." in docs[0].page_content
