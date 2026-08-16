import os
import shutil
import tempfile
from pathlib import Path

# Los tests SHALL correr contra una base de datos, un vector store y una
# carpeta de uploads propios y aislados — nunca contra `backend/data/`, que
# es donde vive la base de datos real de desarrollo/Docker. Esto tiene que
# fijarse por variable de entorno ANTES de importar `app.main` (y con ello
# `app.config`), porque `Settings()` y el engine de SQLAlchemy en
# `document_repo.py` se construyen una única vez al importar el módulo — un
# `monkeypatch` en un fixture llegaría demasiado tarde.
_TEST_DATA_DIR = Path(tempfile.mkdtemp(prefix="ragvault-test-"))
os.environ["SQLITE_PATH"] = str(_TEST_DATA_DIR / "test.db")
os.environ["CHROMA_PERSIST_DIR"] = str(_TEST_DATA_DIR / "chroma")
os.environ["UPLOADS_DIR"] = str(_TEST_DATA_DIR / "uploads")

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.repositories.document_repo import init_db


@pytest.fixture(autouse=True, scope="session")
def _init_test_db():
    """Algunos tests instancian repositorios directamente (sin pasar por
    `client`, que dispara `init_db()` a través del lifespan de la app) —
    sin esto fallarían con "no such table" si son los primeros en
    ejecutarse contra la base de datos de test, recién creada y vacía."""
    init_db()


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def pytest_sessionfinish(session, exitstatus):
    shutil.rmtree(_TEST_DATA_DIR, ignore_errors=True)
