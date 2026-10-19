from fastapi.testclient import TestClient

from app.config import get_settings
from app.data.catalog import clear_catalog_cache, list_classes
from app.domain.models import Role, SimulationRequest
from app.main import create_app
from app.persistence.db import init_db
from app.simulation.profile_composer import compose_profile


def test_catalog_has_thirteen_classes_and_forty_specs(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SIM_ENGINE", "mock")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 't.db'}")
    get_settings.cache_clear()
    clear_catalog_cache()
    classes = list_classes()
    assert len(classes) == 13
    specs = [s for c in classes for s in c.specs]
    assert len(specs) == 40
    canonicals = {s.canonicalId for s in specs}
    assert "demon_hunter_devourer" in canonicals
    assert "evoker_augmentation" in canonicals
    assert "mage_fire" in canonicals
    assert "hunter_beast_mastery" in canonicals
    assert "paladin_retribution" in canonicals
    roles = {s.role for s in specs}
    assert Role.support in roles
    assert Role.tank in roles
    assert Role.healer in roles


def test_builds_current_and_raid_effects(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SIM_ENGINE", "mock")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 't.db'}")
    get_settings.cache_clear()
    clear_catalog_cache()
    init_db()
    client = TestClient(create_app())

    health = client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json()["specCount"] == 40
    assert health.json()["classCount"] == 13

    build = client.get("/api/v1/builds/current")
    assert build.status_code == 200
    body = build.json()
    assert body["patch"] == "12.1.5"
    assert body["clientBuild"] == 70448

    raid = client.get("/api/v1/raid-effects")
    assert raid.status_code == 200
    assert "buffs" in raid.json()


def test_raid_composer_and_aug_personal_only(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SIM_ENGINE", "mock")
    get_settings.cache_clear()
    clear_catalog_cache()
    settings = get_settings()
    from app.data.catalog import get_spec

    shadow = get_spec(258)
    assert shadow is not None
    req = SimulationRequest(
        specId=258,
        fight={"targets": 3, "duration": 300, "mode": "preview"},
        raid={
            "arcaneIntellect": True,
            "battleShout": False,
            "markOfTheWild": True,
            "skyfury": True,
            "chaosBrand": True,
            "mysticTouch": False,
            "bloodlust": {"enabled": True, "atMs": 0},
        },
    )
    composed = compose_profile(
        req,
        settings=settings,
        preset_filename=shadow.presetProfile or "",
        support=shadow.simulationSupport,
        default_hero_talent=shadow.defaultHeroTalent,
        spec=shadow,
    )
    assert "optimal_raid=0" in composed.text
    assert any("battleShout=off" in a for a in composed.assumptions)

    aug = get_spec(1473)
    assert aug is not None and aug.role.value == "SUPPORT"
    assert aug.augmentationModel is not None


def test_mock_aug_and_healer_scaling(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SIM_ENGINE", "mock")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 't.db'}")
    get_settings.cache_clear()
    clear_catalog_cache()
    init_db()
    client = TestClient(create_app())

    # Augmentation is unsupported for SimC but mock validates ok.
    aug = client.post(
        "/api/v1/simulations?sync=true",
        json={
            "specId": 1473,
            "fight": {"targets": 1, "duration": 120, "mode": "preview"},
            "party": {"enabled": False, "members": []},
        },
    )
    assert aug.status_code == 200, aug.text
    result = aug.json()["result"]
    assert result["isDemo"] is True
    assert any("Personal DPS only" in a for a in result.get("assumptions", []))

    aug_party = client.post(
        "/api/v1/simulations?sync=true",
        json={
            "specId": 1473,
            "fight": {"targets": 1, "duration": 120, "mode": "preview"},
            "party": {
                "enabled": True,
                "members": [{"specCanonicalId": "mage_fire", "baselineDps": 100000}],
            },
        },
    )
    assert aug_party.status_code == 200
    party_result = aug_party.json()["result"]
    assert party_result["externalContributionDps"] is not None
    assert party_result["effectiveDps"] > party_result["personalDps"]
