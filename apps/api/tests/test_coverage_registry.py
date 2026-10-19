from fastapi.testclient import TestClient

from app.config import get_settings
from app.data.catalog import clear_catalog_cache, get_spec_by_key, list_classes, list_specs
from app.main import create_app
from app.persistence.db import init_db

REQUIRED_KEYS = {
    "death_knight_blood",
    "death_knight_frost",
    "death_knight_unholy",
    "demon_hunter_havoc",
    "demon_hunter_vengeance",
    "demon_hunter_devourer",
    "druid_balance",
    "druid_feral",
    "druid_guardian",
    "druid_restoration",
    "evoker_augmentation",
    "evoker_devastation",
    "evoker_preservation",
    "hunter_beast_mastery",
    "hunter_marksmanship",
    "hunter_survival",
    "mage_arcane",
    "mage_fire",
    "mage_frost",
    "monk_brewmaster",
    "monk_mistweaver",
    "monk_windwalker",
    "paladin_holy",
    "paladin_protection",
    "paladin_retribution",
    "priest_discipline",
    "priest_holy",
    "priest_shadow",
    "rogue_assassination",
    "rogue_outlaw",
    "rogue_subtlety",
    "shaman_elemental",
    "shaman_enhancement",
    "shaman_restoration",
    "warlock_affliction",
    "warlock_demonology",
    "warlock_destruction",
    "warrior_arms",
    "warrior_fury",
    "warrior_protection",
}


def test_registry_has_13_classes_and_40_specs() -> None:
    clear_catalog_cache()
    classes = list_classes()
    specs = list_specs()
    assert len(classes) == 13
    assert len(specs) == 40
    keys = {s.key for s in specs}
    ids = [s.id for s in specs]
    assert keys == REQUIRED_KEYS
    assert len(ids) == len(set(ids))
    assert all(s.readiness is not None for s in specs)


def test_special_specs_present_and_modeled() -> None:
    arcane = get_spec_by_key("mage_arcane")
    devourer = get_spec_by_key("demon_hunter_devourer")
    aug = get_spec_by_key("evoker_augmentation")
    assert arcane is not None and any(a.simcAction == "arcane_blast" for a in arcane.abilities)
    assert devourer is not None and any(a.simcAction == "collapsing_star" for a in devourer.abilities)
    assert devourer.canAccurate is True
    assert aug is not None and aug.allyModelRequired is True
    assert len(arcane.talentTree.specNodes) > 0
    assert len(devourer.talentTree.apexNodes) > 0


def test_api_coverage_and_fast_estimate(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SIM_ENGINE", "mock")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'cov.db'}")
    get_settings.cache_clear()
    clear_catalog_cache()
    init_db()
    client = TestClient(create_app())

    health = client.get("/api/v1/health").json()
    assert health["classCount"] == 13
    assert health["specCount"] == 40

    build = client.get("/api/v1/builds/current")
    assert build.status_code == 200
    assert build.json()["clientBuild"] == 70448

    specs = client.get("/api/v1/specs")
    assert specs.status_code == 200
    assert len(specs.json()) == 40

    arcane = client.get("/api/v1/specs/mage_arcane")
    assert arcane.status_code == 200
    assert arcane.json()["key"] == "mage_arcane"

    talents = client.get("/api/v1/specs/demon_hunter_devourer/talents")
    assert talents.status_code == 200
    assert talents.json()["talentTree"]["apexNodes"]

    raid = client.get("/api/v1/raid-effects")
    assert raid.status_code == 200
    assert raid.json()["buffs"]

    sim = client.post(
        "/api/v1/simulations?sync=true",
        json={
            "specKey": "mage_arcane",
            "fight": {"targets": 3, "duration": 300, "mode": "fast_estimate"},
        },
    )
    assert sim.status_code == 200, sim.text
    body = sim.json()
    assert body["status"] == "succeeded"
    assert body["result"]["isApproximation"] is True
    assert body["result"]["meanDps"] > 0

    aug = client.post(
        "/api/v1/simulations?sync=true",
        json={
            "specKey": "evoker_augmentation",
            "fight": {
                "targets": 1,
                "duration": 300,
                "mode": "fast_estimate",
                "allies": {"enabled": True, "allyCount": 4, "allyMeanDps": 50000, "buffUptime": 0.85},
            },
        },
    )
    assert aug.status_code == 200, aug.text
    assert aug.json()["result"]["allyAttributedDps"] is not None

    get_settings.cache_clear()
    clear_catalog_cache()


def test_disable_ability_rebuilds_estimate(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SIM_ENGINE", "mock")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'abl.db'}")
    get_settings.cache_clear()
    clear_catalog_cache()
    init_db()
    client = TestClient(create_app())

    base = client.post(
        "/api/v1/simulations?sync=true",
        json={"specKey": "priest_shadow", "fight": {"mode": "fast_estimate", "targets": 1, "duration": 300}},
    ).json()["result"]
    disabled = client.post(
        "/api/v1/simulations?sync=true",
        json={
            "specKey": "priest_shadow",
            "rotation": {"mode": "automatic", "disabledActions": ["mind_blast"]},
            "fight": {"mode": "fast_estimate", "targets": 1, "duration": 300},
        },
    ).json()["result"]
    assert disabled["meanDps"] != base["meanDps"]
    assert all(row["name"] != "mind_blast" for row in disabled["breakdown"])
    get_settings.cache_clear()
    clear_catalog_cache()
