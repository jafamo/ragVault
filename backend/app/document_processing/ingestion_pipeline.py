import time

from app.config import settings
from app.core.cancellation import cancellation_registry
from app.core.logging import get_logger
from app.core.progress import progress_tracker
from app.repositories.document_repo import DocumentRepository
from app.repositories.vector_store import VectorStoreRepository

from .loader_factory import get_loader
from .loaders.base import LoaderParsingError
from .splitter import split_documents

logger = get_logger(__name__)

_EMBED_BATCH_SIZE = 10
_RETRY_BACKOFF_SECONDS = (1, 2, 4)


class IngestionCancelled(Exception):
    pass


def _check_cancelled(document_id: str) -> None:
    if cancellation_registry.is_cancelled(document_id):
        raise IngestionCancelled(document_id)


def _add_chunks_with_retry(vector_store: VectorStoreRepository, document_id: str, chunks) -> None:
    total = len(chunks)
    if total == 0:
        return

    for start in range(0, total, _EMBED_BATCH_SIZE):
        _check_cancelled(document_id)
        batch = chunks[start : start + _EMBED_BATCH_SIZE]
        for attempt in range(1, settings.ingestion_max_retries + 1):
            try:
                vector_store.add_chunks(document_id, batch)
                break
            except Exception:
                if attempt >= settings.ingestion_max_retries:
                    raise
                backoff = _RETRY_BACKOFF_SECONDS[min(attempt - 1, len(_RETRY_BACKOFF_SECONDS) - 1)]
                logger.warning(
                    "embedding_retry",
                    document_id=document_id,
                    attempt=attempt,
                    backoff_seconds=backoff,
                )
                time.sleep(backoff)

        percent = 50 + int((start + len(batch)) / total * 45)
        progress_tracker.update(document_id, "embedding", percent)


def run_ingestion(document_id: str, path: str, filename: str) -> None:
    document_repo = DocumentRepository()
    progress_tracker.start(document_id)
    document_repo.update_status(document_id, "processing")

    try:
        loader = get_loader(filename)
        raw_documents = loader.load(path)
        for doc in raw_documents:
            doc.metadata["source"] = filename
        progress_tracker.update(document_id, "loading", 25)
        _check_cancelled(document_id)

        chunks = split_documents(raw_documents)
        progress_tracker.update(document_id, "chunking", 50)
        _check_cancelled(document_id)

        vector_store = VectorStoreRepository()
        _add_chunks_with_retry(vector_store, document_id, chunks)
        _check_cancelled(document_id)

        progress_tracker.update(document_id, "indexing", 100)
        document_repo.update_status(document_id, "done", chunk_count=len(chunks))
        progress_tracker.complete(document_id)
        logger.info(
            "document_ingested", document_id=document_id, filename=filename, chunk_count=len(chunks)
        )

    except IngestionCancelled:
        document_repo.update_status(document_id, "cancelled")
        progress_tracker.fail(document_id)
        logger.info("document_ingestion_cancelled", document_id=document_id, filename=filename)

    except LoaderParsingError as exc:
        document_repo.update_status(document_id, "error", error_message=str(exc))
        progress_tracker.fail(document_id)
        logger.warning(
            "document_ingestion_parsing_error",
            document_id=document_id,
            filename=filename,
            error=str(exc),
        )

    except Exception:
        document_repo.update_status(
            document_id, "error", error_message="Error interno durante la ingesta del documento"
        )
        progress_tracker.fail(document_id)
        logger.exception("document_ingestion_failed", document_id=document_id, filename=filename)

    finally:
        cancellation_registry.clear(document_id)
