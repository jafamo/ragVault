from app.repositories.document_repo import DocumentRepository
from app.repositories.stats_repo import KNOWN_STATUSES, StatsRepository
from app.repositories.tag_repo import TagRepository


def test_by_status_includes_all_known_statuses_with_zero_default():
    counts = StatsRepository().by_status()

    assert set(KNOWN_STATUSES) <= set(counts.keys())
    assert all(count >= 0 for count in counts.values())


def test_by_status_reflects_new_document():
    before = StatsRepository().by_status()
    DocumentRepository().create(filename="c.pdf", format="pdf")
    after = StatsRepository().by_status()

    assert after["queued"] == before["queued"] + 1


def test_by_format_counts_new_document():
    before = StatsRepository().by_format().get("odt", 0)
    DocumentRepository().create(filename="d.odt", format="odt")
    after = StatsRepository().by_format().get("odt", 0)

    assert after == before + 1


def test_errors_only_returns_error_status_documents():
    document = DocumentRepository().create(filename="e.pdf", format="pdf")
    DocumentRepository().update_status(document.id, "error", error_message="boom")

    errors = StatsRepository().errors()

    matching = [doc for doc in errors if doc.id == document.id]
    assert len(matching) == 1
    assert matching[0].error_message == "boom"


def test_timeline_counts_recently_uploaded_document():
    DocumentRepository().create(filename="f.pdf", format="pdf")

    timeline = StatsRepository().timeline()

    assert timeline[5] >= 1
    assert timeline[365] >= timeline[5]


def test_by_tag_includes_sin_tag_bucket_for_untagged_document():
    DocumentRepository().create(filename="g.pdf", format="pdf")

    counts = StatsRepository().by_tag()

    assert "sin_tag" in counts
    assert counts["sin_tag"] >= 1


def test_by_tag_counts_tagged_document():
    document = DocumentRepository().create(filename="h.pdf", format="pdf")
    TagRepository().assign(document.id, ["temática-x"])

    counts = StatsRepository().by_tag()

    assert counts["temática-x"] >= 1
