from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from app.config import Settings, get_settings
from app.domain.models import (
    Ability,
    AugmentationModel,
    HeroTalentTree,
    Role,
    SpecCoverage,
    Specialization,
    SimulationSupport,
    TalentTree,
    WowClass,
)


def _load_raw(settings: Settings) -> dict:
    path = Path(settings.game_data_dir) / "catalog" / settings.game_version / "catalog.json"
    if not path.is_file():
        raise FileNotFoundError(f"Game catalog not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_spec(class_id: int, class_name: str, raw: dict) -> Specialization:
    heroes = [HeroTalentTree.model_validate(h) for h in raw.get("heroTalentTrees") or []]
    abilities = [Ability.model_validate(a) for a in raw.get("abilities") or []]
    coverage = SpecCoverage.model_validate(raw.get("coverage") or {})
    aug = None
    if raw.get("augmentationModel"):
        aug = AugmentationModel.model_validate(raw["augmentationModel"])
    return Specialization(
        id=int(raw["id"]),
        classId=class_id,
        className=class_name,
        name=raw["name"],
        canonicalId=raw.get("canonicalId"),
        role=Role(raw["role"]),
        resourceType=raw.get("resourceType") or "Unknown",
        heroTalentTrees=heroes,
        abilities=abilities,
        talentTree=TalentTree(heroTrees=heroes),
        simulationSupport=SimulationSupport(raw["simulationSupport"]),
        presetProfile=raw.get("presetProfile"),
        defaultHeroTalent=raw.get("defaultHeroTalent"),
        notes=raw.get("notes"),
        apexNotes=raw.get("apexNotes"),
        coverage=coverage,
        augmentationModel=aug,
    )


@lru_cache
def get_catalog_raw() -> dict:
    return _load_raw(get_settings())


def list_versions(settings: Settings | None = None) -> list[dict]:
    settings = settings or get_settings()
    raw = _load_raw(settings)
    return [
        {
            "id": raw["gameVersion"],
            "dataSnapshotId": raw["dataSnapshotId"],
            "simcCommit": raw["simcCommit"],
            "clientBuild": raw.get("clientBuild"),
            "hotfixDate": raw.get("hotfixDate"),
            "level": raw.get("level", 90),
            "sources": raw.get("sources") or [],
        }
    ]


def current_build_metadata(settings: Settings | None = None) -> dict:
    versions = list_versions(settings)
    return versions[0] if versions else {}


def list_classes(settings: Settings | None = None) -> list[WowClass]:
    settings = settings or get_settings()
    raw = _load_raw(settings)
    classes: list[WowClass] = []
    for c in raw["classes"]:
        specs = [_parse_spec(c["id"], c["name"], s) for s in c.get("specs") or []]
        classes.append(
            WowClass(id=c["id"], name=c["name"], color=c.get("color") or "#888888", specs=specs)
        )
    return classes


def get_class(class_id: int, settings: Settings | None = None) -> WowClass | None:
    for wow_class in list_classes(settings):
        if wow_class.id == class_id:
            return wow_class
    return None


def get_spec(spec_id: int, settings: Settings | None = None) -> Specialization | None:
    for wow_class in list_classes(settings):
        for spec in wow_class.specs:
            if spec.id == spec_id:
                return spec
    return None


def get_spec_by_canonical(canonical_id: str, settings: Settings | None = None) -> Specialization | None:
    for wow_class in list_classes(settings):
        for spec in wow_class.specs:
            if spec.canonicalId == canonical_id:
                return spec
    return None


def raid_effects() -> dict:
    return {
        "buffs": [
            {"id": "arcaneIntellect", "name": "Arcane Intellect", "effect": "+3% Intellect"},
            {"id": "battleShout", "name": "Battle Shout", "effect": "+5% Attack Power"},
            {"id": "markOfTheWild", "name": "Mark of the Wild", "effect": "+3% Versatility"},
            {"id": "skyfury", "name": "Skyfury", "effect": "+2% Mastery"},
            {
                "id": "bloodlust",
                "name": "Bloodlust / Heroism",
                "effect": "+30% Haste for 40s",
                "timed": True,
            },
        ],
        "debuffs": [
            {"id": "chaosBrand", "name": "Chaos Brand", "effect": "+3% magic damage taken"},
            {"id": "mysticTouch", "name": "Mystic Touch", "effect": "+5% physical damage taken"},
        ],
        "notes": "Toggles are independent; do not collapse into a single raidDamageMultiplier.",
    }


def clear_catalog_cache() -> None:
    get_catalog_raw.cache_clear()
