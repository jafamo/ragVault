def test_create_and_list_session(client):
    created = client.post("/sessions")
    assert created.status_code == 200
    session_id = created.json()["id"]

    listed = client.get("/sessions")
    assert listed.status_code == 200
    assert any(s["id"] == session_id for s in listed.json())


def test_get_unknown_session_returns_404(client):
    response = client.get("/sessions/no-existe")
    assert response.status_code == 404


def test_get_messages_of_unknown_session_returns_404(client):
    response = client.get("/sessions/no-existe/messages")
    assert response.status_code == 404


def test_delete_session_cascades_and_then_404(client):
    session_id = client.post("/sessions").json()["id"]

    deleted = client.delete(f"/sessions/{session_id}")
    assert deleted.status_code == 204

    assert client.get(f"/sessions/{session_id}").status_code == 404
    assert client.get(f"/sessions/{session_id}/messages").status_code == 404


def test_delete_unknown_session_returns_404(client):
    assert client.delete("/sessions/no-existe").status_code == 404
