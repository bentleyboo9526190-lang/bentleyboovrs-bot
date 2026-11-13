from __future__ import annotations

import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient

PROJECT_DIR = Path(__file__).resolve().parents[1] / "bentleyboovr"
sys.path.insert(0, str(PROJECT_DIR))

import companion  # noqa: E402


client = TestClient(companion.app)


def setup_function() -> None:
    companion.pending_requests.clear()


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_request_creates_confirmation_prompt() -> None:
    response = client.post("/request", json={"text": "show me the lobby"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "awaiting_confirmation"
    assert "show me the lobby" in data["spoken_response"]
    assert data["request_id"] in companion.pending_requests


def test_confirm_yes_records_approval_without_game_action() -> None:
    created = client.post("/request", json={"text": "test action"}).json()
    response = client.post(
        "/confirm",
        json={"request_id": created["request_id"], "approved": True},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "approved"
    assert "has not performed an in-game action" in response.json()["message"]
    assert created["request_id"] not in companion.pending_requests


def test_confirm_no_records_decline() -> None:
    created = client.post("/request", json={"text": "test action"}).json()
    response = client.post(
        "/confirm",
        json={"request_id": created["request_id"], "approved": False},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "declined"


def test_confirm_unknown_request_returns_404() -> None:
    response = client.post(
        "/confirm",
        json={"request_id": "not-a-real-id", "approved": False},
    )
    assert response.status_code == 404


def test_ai_speech_requires_server_side_key(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    response = client.post("/speech", json={"text": "Hello from BentleyBooVR"})
    assert response.status_code == 503
    assert "not configured" in response.json()["detail"]
