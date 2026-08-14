from langchain_core.documents import Document

from app.config import settings
from app.document_processing.splitter import split_documents


def test_long_document_is_split_into_multiple_chunks():
    long_text = "Frase de prueba. " * (settings.chunk_size // 10)
    chunks = split_documents([Document(page_content=long_text)])

    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk.page_content) <= settings.chunk_size + settings.chunk_overlap


def test_short_document_stays_as_one_chunk():
    chunks = split_documents([Document(page_content="Texto corto.")])
    assert len(chunks) == 1
