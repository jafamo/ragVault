import httpx
import respx
from fastapi.testclient import TestClient

from app.config import settings


def test_health_ollama_reachable(client: TestClient):
    with respx.mock:
        respx.get(f"{settings.ollama_base_url}/api/tags").mock(
            return_value=httpx.Response(200, json={"models": []})
        )
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "ollama": "reachable"}


def test_health_ollama_unreachable(client: TestClient):
    with respx.mock:
        respx.get(f"{settings.ollama_base_url}/api/tags").mock(
            side_effect=httpx.ConnectError("connection refused")
        )
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "ollama": "unreachable"}
