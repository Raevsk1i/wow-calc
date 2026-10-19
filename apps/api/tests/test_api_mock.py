from fastapi.testclient import TestClient

from app.config import get_settings
from app.data.catalog import clear_catalog_cache
from app.main import create_app
from app.persistence.db import init_db


def test_health_and_mock_simulation(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("SIM_ENGINE", "mock")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    get_settings.cache_clear()
    clear_catalog_cache()
    init_db()
    app = create_app()
    client = TestClient(app)

    health = client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json()["engine"] == "mock"
    assert health.json()["specCount"] == 40

    classes = client.get("/api/v1/classes")
    assert classes.status_code == 200
    payload = classes.json()
    assert len(payload) == 13
    assert any(c["name"] == "Priest" for c in payload)
    assert any(c["name"] == "Mage" for c in payload)
    assert any(c["name"] == "Hunter" for c in payload)
    assert any(c["name"] == "Paladin" for c in payload)

    sim = client.post(
        "/api/v1/simulations?sync=true",
        json={
            "specId": 258,
            "fight": {"targets": 5, "duration": 180, "mode": "preview"},
            "raid": {"battleShout": True, "arcaneIntellect": True},
        },
    )
    assert sim.status_code == 200, sim.text
    body = sim.json()
    assert body["status"] == "succeeded"
    assert body["result"]["isDemo"] is True
    assert body["result"]["meanDps"] > 0
    assert body["result"]["targets"] == 5
    assert body["result"]["personalDps"] is not None
    assert "assumptions" in body["result"]

    # Legacy mode alias still accepted
    legacy = client.post(
        "/api/v1/simulations?sync=true",
        json={"specId": 258, "fight": {"targets": 1, "duration": 120, "mode": "quick"}},
    )
    assert legacy.status_code == 200

    get_settings.cache_clear()
