import threading
from dataclasses import dataclass


@dataclass
class IngestionProgress:
    stage: str
    percent: int


class IngestionProgressTracker:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._progress: dict[str, IngestionProgress] = {}

    def start(self, document_id: str) -> None:
        with self._lock:
            self._progress[document_id] = IngestionProgress(stage="loading", percent=0)

    def update(self, document_id: str, stage: str, percent: int) -> None:
        with self._lock:
            self._progress[document_id] = IngestionProgress(stage=stage, percent=percent)

    def complete(self, document_id: str) -> None:
        with self._lock:
            self._progress[document_id] = IngestionProgress(stage="done", percent=100)

    def fail(self, document_id: str) -> None:
        with self._lock:
            self._progress.pop(document_id, None)

    def get(self, document_id: str) -> IngestionProgress | None:
        with self._lock:
            return self._progress.get(document_id)


progress_tracker = IngestionProgressTracker()
