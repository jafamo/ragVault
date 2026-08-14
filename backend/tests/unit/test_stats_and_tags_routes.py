import io


def test_stats_endpoints_return_200(client):
    client.post(
        "/upload",
        files={"file": ("i.txt", io.BytesIO(b"contenido"), "text/plain")},
    )

    for path in ["/stats/by-format", "/stats/by-status", "/stats/errors", "/stats/timeline", "/stats/by-tag"]:
        response = client.get(path)
        assert response.status_code == 200, path


def test_assign_and_list_document_tags(client):
    upload = client.post(
        "/upload",
        files={"file": ("j.txt", io.BytesIO(b"contenido"), "text/plain")},
    )
    document_id = upload.json()["id"]

    assign_response = client.post(f"/documents/{document_id}/tags", json={"tags": ["informes", "2024"]})
    assert assign_response.status_code == 200
    assert sorted(assign_response.json()["tags"]) == ["2024", "informes"]

    list_response = client.get(f"/documents/{document_id}/tags")
    assert list_response.status_code == 200
    assert sorted(list_response.json()["tags"]) == ["2024", "informes"]


def test_assign_tags_unknown_document_returns_404(client):
    response = client.post("/documents/no-existe/tags", json={"tags": ["x"]})
    assert response.status_code == 404


def test_list_tags_unknown_document_returns_404(client):
    response = client.get("/documents/no-existe/tags")
    assert response.status_code == 404
