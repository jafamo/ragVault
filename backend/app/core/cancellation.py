import threading


class CancellationRegistry:
    """Señaliza la cancelación de una ingesta en curso. En memoria, sin
    persistencia — igual que `IngestionProgressTracker`, del que es
    consultado por `run_ingestion` entre etapas del pipeline."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._cancelled: set[str] = set()

    def request_cancel(self, document_id: str) -> None:
        with self._lock:
            self._cancelled.add(document_id)

    def is_cancelled(self, document_id: str) -> bool:
        with self._lock:
            return document_id in self._cancelled

    def clear(self, document_id: str) -> None:
        with self._lock:
            self._cancelled.discard(document_id)


cancellation_registry = CancellationRegistry()
