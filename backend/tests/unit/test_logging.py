import json
import logging

import httpx
import respx
from fastapi.testclient import TestClient

from app.config import settings


def test_request_id_present_in_log_and_response(client: TestClient, caplog):
    with respx.mock:
        respx.get(f"{settings.ollama_base_url}/api/tags").mock(
            side_effect=httpx.ConnectError("connection refused")
        )
        with caplog.at_level(logging.WARNING):
            response = client.get("/health")

    request_id = response.headers["X-Request-ID"]
    assert request_id

    matching = [
        json.loads(record.getMessage())
        for record in caplog.records
        if request_id in record.getMessage()
    ]
    assert matching, "expected a log line correlated with the request's request_id"
    assert matching[0]["request_id"] == request_id
