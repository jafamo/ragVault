import threading

from app.core.progress import IngestionProgressTracker


def test_start_update_complete_reflected_in_get():
    tracker = IngestionProgressTracker()
    tracker.start("doc-1")
    assert tracker.get("doc-1").stage == "loading"
    assert tracker.get("doc-1").percent == 0

    tracker.update("doc-1", "embedding", 60)
    assert tracker.get("doc-1").stage == "embedding"
    assert tracker.get("doc-1").percent == 60

    tracker.complete("doc-1")
    assert tracker.get("doc-1").stage == "done"
    assert tracker.get("doc-1").percent == 100


def test_fail_removes_progress_entry():
    tracker = IngestionProgressTracker()
    tracker.start("doc-1")
    tracker.fail("doc-1")
    assert tracker.get("doc-1") is None


def test_get_unknown_document_returns_none():
    tracker = IngestionProgressTracker()
    assert tracker.get("unknown") is None


def test_concurrent_updates_do_not_corrupt_state():
    tracker = IngestionProgressTracker()
    tracker.start("doc-1")

    def worker(percent):
        tracker.update("doc-1", "embedding", percent)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(50)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    progress = tracker.get("doc-1")
    assert progress is not None
    assert progress.stage == "embedding"
    assert 0 <= progress.percent < 50
