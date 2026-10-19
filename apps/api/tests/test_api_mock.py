from pathlib import Path

from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app
from app.persistence.db import init_db


def test_health_and_mock_simulation(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("SIM_ENGINE", "mock")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    get_settings.cache_clear()
    init_db()
    app = create_app()
    client = TestClient(app)

    health = client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json()["engine"] == "mock"

    classes = client.get("/api/v1/classes")
    assert classes.status_code == 200
    assert any(c["name"] == "Priest" for c in classes.json())

    sim = client.post(
        "/api/v1/simulations?sync=true",
        json={
            "specId": 258,
            "fight": {"targets": 5, "duration": 180, "mode": "quick"},
        },
    )
    assert sim.status_code == 200, sim.text
    body = sim.json()
    assert body["status"] == "succeeded"
    assert body["result"]["isDemo"] is True
    assert body["result"]["meanDps"] > 0
    assert body["result"]["targets"] == 5

    get_settings.cache_clear()
