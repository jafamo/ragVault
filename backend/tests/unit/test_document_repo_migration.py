import tempfile
from pathlib import Path

from sqlalchemy import create_engine, inspect, text

from app.repositories import document_repo


def test_init_db_backfills_missing_columns_on_pre_existing_database(monkeypatch):
    """Regresión: una base de datos creada antes de que `status`,
    `error_message`, `size_bytes` o `absolute_path` existieran en el
    modelo debe seguir arrancando sin `OperationalError: no such column`
    tras un despliegue nuevo, con las filas ya existentes marcadas como
    `'done'` (se subieron con la ingesta síncrona original, sin estados
    intermedios)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "legacy.db"
        legacy_engine = create_engine(f"sqlite:///{db_path}")
        with legacy_engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE TABLE documents ("
                    "id VARCHAR PRIMARY KEY, filename VARCHAR, format VARCHAR, "
                    "uploaded_at DATETIME, chunk_count INTEGER)"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO documents (id, filename, format, chunk_count) "
                    "VALUES ('doc-1', 'contrato.pdf', 'pdf', 12)"
                )
            )
        legacy_engine.dispose()

        test_engine = create_engine(f"sqlite:///{db_path}")
        monkeypatch.setattr(document_repo, "_engine", test_engine)
        monkeypatch.setattr(document_repo, "_SessionLocal", document_repo.sessionmaker(bind=test_engine))

        document_repo.init_db()

        inspector = inspect(test_engine)
        columns = {col["name"] for col in inspector.get_columns("documents")}
        assert {"status", "error_message", "size_bytes", "absolute_path"} <= columns

        with test_engine.connect() as connection:
            row = connection.execute(
                text("SELECT status, error_message, size_bytes, absolute_path FROM documents WHERE id = 'doc-1'")
            ).one()
        assert row.status == "done"
        assert row.error_message is None
        assert row.size_bytes is None
        assert row.absolute_path is None

        # Idempotente: correr init_db otra vez sobre el esquema ya migrado no falla.
        document_repo.init_db()
