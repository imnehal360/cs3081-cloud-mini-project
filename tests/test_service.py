
import json

import service.main as service
from fastapi.testclient import TestClient


class FakeRunner:
    def __init__(self, output):
        self.output = output

    def predict(self, text, max_new_tokens=80):
        return self.output


def test_health_endpoint():
    client = TestClient(service.app)
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json()["status"] == "alive"


def test_readiness_when_model_not_loaded(monkeypatch):
    monkeypatch.setattr(service, "ready", False)

    client = TestClient(service.app)
    response = client.get("/readyz")

    assert response.status_code == 503


def test_valid_model_response(monkeypatch):
    expected = {
        "intent": "alarm_set",
        "date": "tomorrow",
        "time": "seven am",
        "place": None,
    }

    monkeypatch.setattr(service, "ready", True)
    monkeypatch.setattr(
        service,
        "runner",
        FakeRunner(json.dumps(expected)),
    )
    monkeypatch.setenv("MODEL_VERSION", "v1")

    client = TestClient(service.app)

    response = client.post(
        "/parse",
        json={"text": "set alarm for seven am tomorrow"},
    )

    assert response.status_code == 200
    assert response.json() == expected
    assert response.headers["x-model-version"] == "v1"
    assert response.headers["x-served-by"]


def test_invalid_model_response(monkeypatch):
    monkeypatch.setattr(service, "ready", True)
    monkeypatch.setattr(
        service,
        "runner",
        FakeRunner("not json"),
    )

    client = TestClient(service.app)

    response = client.post(
        "/parse",
        json={"text": "set an alarm"},
    )

    assert response.status_code == 500
    assert response.json() == {
        "error": "invalid_model_output"
    }


def test_fault_injection(monkeypatch):
    monkeypatch.setattr(service, "ready", True)
    monkeypatch.setattr(
        service,
        "runner",
        FakeRunner(json.dumps({
            "intent": "alarm_set",
            "date": None,
            "time": None,
            "place": None,
        })),
    )
    monkeypatch.setenv("FAULT_INJECT", "1")

    client = TestClient(service.app)

    response = client.post(
        "/parse",
        json={"text": "set an alarm"},
    )

    assert response.status_code == 500
    assert response.json() == {
        "error": "invalid_model_output"
    }
