from app.core.cancellation import CancellationRegistry


def test_not_cancelled_by_default():
    registry = CancellationRegistry()
    assert registry.is_cancelled("doc-1") is False


def test_request_cancel_marks_document_cancelled():
    registry = CancellationRegistry()
    registry.request_cancel("doc-1")
    assert registry.is_cancelled("doc-1") is True


def test_clear_removes_cancellation():
    registry = CancellationRegistry()
    registry.request_cancel("doc-1")
    registry.clear("doc-1")
    assert registry.is_cancelled("doc-1") is False


def test_cancellation_is_scoped_per_document():
    registry = CancellationRegistry()
    registry.request_cancel("doc-1")
    assert registry.is_cancelled("doc-2") is False
