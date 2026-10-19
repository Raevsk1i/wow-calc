from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from app.config import Settings, get_settings
from app.domain.models import (
    Ability,
    HeroTalentTree,
    Role,
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
    return Specialization(
        id=int(raw["id"]),
        classId=class_id,
        className=class_name,
        name=raw["name"],
        role=Role(raw["role"]),
        resourceType=raw.get("resourceType") or "Unknown",
        heroTalentTrees=heroes,
        abilities=abilities,
        talentTree=TalentTree(heroTrees=heroes),
        simulationSupport=SimulationSupport(raw["simulationSupport"]),
        presetProfile=raw.get("presetProfile"),
        defaultHeroTalent=raw.get("defaultHeroTalent"),
        notes=raw.get("notes"),
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
            "sources": raw.get("sources") or [],
        }
    ]


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


def clear_catalog_cache() -> None:
    get_catalog_raw.cache_clear()
