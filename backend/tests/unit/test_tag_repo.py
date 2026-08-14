from app.repositories.document_repo import DocumentRepository
from app.repositories.tag_repo import TagRepository


def test_assign_creates_and_reuses_tags_case_insensitively():
    document = DocumentRepository().create(filename="a.pdf", format="pdf")
    tag_repo = TagRepository()

    first = tag_repo.assign(document.id, ["Facturas", "2024"])
    second = tag_repo.assign(document.id, ["facturas", "urgente"])

    assert sorted(first) == ["2024", "Facturas"]
    assert sorted(second) == ["2024", "Facturas", "urgente"]


def test_assign_unknown_document_returns_none():
    tag_repo = TagRepository()

    result = tag_repo.assign("no-existe", ["x"])

    assert result is None


def test_list_for_document_returns_assigned_tags():
    document = DocumentRepository().create(filename="b.pdf", format="pdf")
    tag_repo = TagRepository()
    tag_repo.assign(document.id, ["contratos"])

    tags = tag_repo.list_for_document(document.id)

    assert tags == ["contratos"]


def test_list_for_document_unknown_returns_none():
    assert TagRepository().list_for_document("no-existe") is None
