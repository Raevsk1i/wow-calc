from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from app.config import Settings, get_settings
from app.domain.models import (
    Ability,
    HeroTalentTree,
    ReadinessStatus,
    Role,
    Specialization,
    TalentTree,
    WowClass,
)


def _load_raw(settings: Settings) -> dict:
    path = Path(settings.game_data_dir) / "catalog" / settings.game_version / "catalog.json"
    if not path.is_file():
        raise FileNotFoundError(f"Game catalog not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _load_json(settings: Settings, name: str) -> dict:
    path = Path(settings.game_data_dir) / "catalog" / settings.game_version / name
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_spec(class_id: int, class_name: str, class_name_ru: str | None, raw: dict) -> Specialization:
    heroes = [HeroTalentTree.model_validate(h) for h in raw.get("heroTalentTrees") or []]
    abilities = [Ability.model_validate(a) for a in raw.get("abilities") or []]
    readiness = ReadinessStatus(raw.get("readiness") or raw["simulationSupport"])
    return Specialization(
        id=int(raw["id"]),
        key=raw.get("key") or f"{class_name.lower().replace(' ', '_')}_{raw['name'].lower()}",
        classId=class_id,
        className=class_name,
        classNameRu=class_name_ru,
        name=raw["name"],
        nameRu=raw.get("nameRu"),
        role=Role(raw["role"]),
        attackType=raw.get("attackType") or "melee",
        primaryStat=raw.get("primaryStat") or "agility",
        resourceType=raw.get("resourceType") or "Unknown",
        heroTalentTrees=heroes,
        abilities=abilities,
        talentTree=TalentTree(heroTrees=heroes),
        simulationSupport=readiness,
        readiness=readiness,
        canAccurate=bool(raw.get("canAccurate")),
        canFastEstimate=bool(raw.get("canFastEstimate", True)),
        presetProfile=raw.get("presetProfile"),
        defaultHeroTalent=raw.get("defaultHeroTalent"),
        notes=raw.get("notes"),
        allyModelRequired=bool(raw.get("allyModelRequired")),
        damageActivityShareDefault=float(raw.get("damageActivityShareDefault") or 1.0),
        offenseTank=bool(raw.get("offenseTank")),
    )


@lru_cache
def get_catalog_raw() -> dict:
    return _load_raw(get_settings())


@lru_cache
def get_ruleset() -> dict:
    return _load_json(get_settings(), "ruleset.json")


@lru_cache
def get_raid_effects() -> dict:
    return _load_json(get_settings(), "raid_effects.json")


@lru_cache
def get_estimate_baselines() -> dict:
    return _load_json(get_settings(), "estimate_baselines.json")


def list_versions(settings: Settings | None = None) -> list[dict]:
    settings = settings or get_settings()
    raw = _load_raw(settings)
    ruleset = _load_json(settings, "ruleset.json")
    return [
        {
            "id": raw["gameVersion"],
            "dataSnapshotId": raw["dataSnapshotId"],
            "simcCommit": raw["simcCommit"],
            "clientBuild": raw.get("clientBuild") or ruleset.get("clientBuild"),
            "hotfixDate": raw.get("hotfixDate") or ruleset.get("hotfixDate"),
            "region": raw.get("region") or ruleset.get("region"),
            "verifiedAt": raw.get("verifiedAt") or ruleset.get("verifiedAt"),
            "confidence": raw.get("confidence") or ruleset.get("confidence"),
            "aplRevision": raw.get("aplRevision") or ruleset.get("aplRevision"),
            "sources": raw.get("sources") or [],
        }
    ]


def get_current_build(settings: Settings | None = None) -> dict:
    versions = list_versions(settings)
    ruleset = get_ruleset() if settings is None else _load_json(settings, "ruleset.json")
    base = versions[0] if versions else {}
    return {**ruleset, **base}


def list_classes(settings: Settings | None = None) -> list[WowClass]:
    settings = settings or get_settings()
    raw = _load_raw(settings)
    classes: list[WowClass] = []
    for c in raw["classes"]:
        specs = [
            _parse_spec(c["id"], c["name"], c.get("nameRu"), s) for s in c.get("specs") or []
        ]
        classes.append(
            WowClass(
                id=c["id"],
                name=c["name"],
                nameRu=c.get("nameRu"),
                color=c.get("color") or "#888888",
                specs=specs,
            )
        )
    return classes


def list_specs(settings: Settings | None = None) -> list[Specialization]:
    out: list[Specialization] = []
    for wow_class in list_classes(settings):
        out.extend(wow_class.specs)
    return out


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


def get_spec_by_key(spec_key: str, settings: Settings | None = None) -> Specialization | None:
    key = spec_key.strip().lower()
    for wow_class in list_classes(settings):
        for spec in wow_class.specs:
            if spec.key == key:
                return spec
    return None


def resolve_spec(
    *,
    spec_id: int | None = None,
    spec_key: str | None = None,
    settings: Settings | None = None,
) -> Specialization | None:
    if spec_key:
        found = get_spec_by_key(spec_key, settings)
        if found:
            return found
    if spec_id is not None:
        return get_spec(spec_id, settings)
    return None


def clear_catalog_cache() -> None:
    get_catalog_raw.cache_clear()
    get_ruleset.cache_clear()
    get_raid_effects.cache_clear()
    get_estimate_baselines.cache_clear()
