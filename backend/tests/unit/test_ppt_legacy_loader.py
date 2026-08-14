import subprocess
from pathlib import Path

import pytest

from app.document_processing.loaders.base import LoaderParsingError
from app.document_processing.loaders.ppt_legacy_loader import PptLegacyLoader

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def test_ppt_legacy_loader_wraps_conversion_failure_as_parsing_error(monkeypatch):
    def fake_run(*args, **kwargs):
        raise subprocess.CalledProcessError(returncode=1, cmd="soffice")

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(LoaderParsingError):
        PptLegacyLoader().load(str(FIXTURES / "corrupt.docx"))


def test_ppt_legacy_loader_missing_soffice_binary_raises_parsing_error(monkeypatch):
    def fake_run(*args, **kwargs):
        raise FileNotFoundError("soffice binary not found")

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(LoaderParsingError):
        PptLegacyLoader().load(str(FIXTURES / "corrupt.docx"))
