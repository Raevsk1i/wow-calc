from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from redis import Redis
from rq.job import Job

from app.config import get_settings
from app.data.catalog import (
    get_class,
    get_current_build,
    get_raid_effects,
    get_spec,
    get_spec_by_key,
    list_classes,
    list_specs,
    list_versions,
    resolve_spec,
)
from app.domain.cache_keys import simulation_cache_key
from app.domain.comparison import compare_results
from app.domain.models import (
    BuildRecord,
    ComparisonRequest,
    ComparisonResult,
    ExplainRequest,
    JobStatus,
    SimulationJobView,
    SimulationMode,
    SimulationRequest,
    SimulationResult,
    StatWeightsRequest,
    TalentImportRequest,
    TalentImportResult,
)
from app.domain.talents import export_talent_passthrough, import_talent_string
from app.jobs.queue import get_queue, get_redis
from app.jobs.tasks import find_cached_job, run_simulation_job
from app.persistence.db import BuildRow, ComparisonRow, SimulationJobRow, get_session, utcnow
from app.simulation.factory import get_engine, get_engine_for_request
from app.simulation.fast_estimate import FastEstimateEngine

router = APIRouter()


def _job_view(row: SimulationJobRow) -> SimulationJobView:
    result = None
    if row.result_json:
        result = SimulationResult.model_validate_json(row.result_json)
    return SimulationJobView(
        id=row.id,
        status=JobStatus(row.status),
        createdAt=row.created_at.isoformat(),
        updatedAt=row.updated_at.isoformat(),
        request=SimulationRequest.model_validate_json(row.request_json),
        result=result,
        error=row.error,
        progress=1.0 if row.status == JobStatus.succeeded.value else None,
    )


def _resolve_spec_param(spec_id: str):
    if spec_id.isdigit():
        spec = get_spec(int(spec_id))
    else:
        spec = get_spec_by_key(spec_id)
    if spec is None:
        raise HTTPException(status_code=404, detail={"code": "spec_not_found", "message": "Spec not found"})
    return spec


@router.get("/health")
def health() -> dict[str, Any]:
    settings = get_settings()
    engine = get_engine(settings)
    build = get_current_build(settings)
    return {
        "ok": True,
        "app": settings.app_name,
        "gameVersion": settings.game_version,
        "engine": engine.name,
        "dataSnapshotId": settings.data_snapshot_id,
        "clientBuild": build.get("clientBuild"),
        "hotfixDate": build.get("hotfixDate"),
        "region": build.get("region"),
        "specCount": len(list_specs(settings)),
        "classCount": len(list_classes(settings)),
    }


@router.get("/builds/current")
def builds_current() -> dict[str, Any]:
    return get_current_build()


@router.get("/game/versions")
def game_versions() -> list[dict[str, Any]]:
    return list_versions()


@router.get("/classes")
def classes() -> list[dict[str, Any]]:
    return [c.model_dump(mode="json") for c in list_classes()]


@router.get("/classes/{class_id}/specs")
def class_specs(class_id: int) -> list[dict[str, Any]]:
    wow_class = get_class(class_id)
    if wow_class is None:
        raise HTTPException(status_code=404, detail={"code": "class_not_found", "message": "Class not found"})
    return [s.model_dump(mode="json") for s in wow_class.specs]


@router.get("/specs")
def specs() -> list[dict[str, Any]]:
    return [s.model_dump(mode="json") for s in list_specs()]


@router.get("/specs/{spec_id}")
def spec_detail(spec_id: str) -> dict[str, Any]:
    return _resolve_spec_param(spec_id).model_dump(mode="json")


@router.get("/specs/{spec_id}/talents")
def spec_talents(spec_id: str) -> dict[str, Any]:
    spec = _resolve_spec_param(spec_id)
    return {
        "specId": spec.id,
        "specKey": spec.key,
        "heroTalentTrees": [h.model_dump(mode="json") for h in spec.heroTalentTrees],
        "talentTree": spec.talentTree.model_dump(mode="json"),
        "notes": (
            "Full interactive node graph requires Blizzard Game Data API snapshot sync. "
            "Current release supports hero talent selection + Blizzard talent string import for SimC, "
            "plus a lightweight editor over curated nodes when present."
        ),
        "readiness": (spec.readiness or spec.simulationSupport).value,
    }


@router.get("/specs/{spec_id}/abilities")
def spec_abilities(spec_id: str) -> list[dict[str, Any]]:
    spec = _resolve_spec_param(spec_id)
    return [a.model_dump(mode="json") for a in spec.abilities]


@router.get("/specs/{spec_id}/apl")
@router.get("/specs/{spec_id}/rotations/default")
def spec_apl(spec_id: str) -> dict[str, Any]:
    spec = _resolve_spec_param(spec_id)
    actions = [a.simcAction for a in spec.abilities if a.category.value in {"active", "required"}]
    return {
        "specId": spec.id,
        "specKey": spec.key,
        "mode": "automatic",
        "profiles": ["automatic", "burst_focus", "sustained", "aoe_optimization", "custom"],
        "actions": actions,
        "presetProfile": spec.presetProfile,
        "source": "curated catalog + SimulationCraft default APL at runtime",
        "aplRevision": get_current_build().get("aplRevision"),
    }


@router.get("/specs/{spec_id}/gear-presets")
def spec_gear_presets(spec_id: str) -> list[dict[str, Any]]:
    spec = _resolve_spec_param(spec_id)
    if not spec.presetProfile:
        return [
            {
                "id": "custom",
                "name": "Custom Stats",
                "profile": None,
                "source": "No MID preset on this pin — use Fast Estimate + custom ratings",
                "warning": "Accurate SimC unavailable until a preset is imported",
            }
        ]
    return [
        {
            "id": "high",
            "name": "High Gear (MID1)",
            "profile": spec.presetProfile,
            "source": "SimulationCraft profiles/MID1",
        },
        {
            "id": "mid",
            "name": "Mid Gear",
            "profile": spec.presetProfile,
            "source": "Same MID1 profile (documented placeholder until PreRaids exists for this pin)",
            "warning": "Mid currently aliases MID1 High for this data snapshot.",
        },
        {
            "id": "entry",
            "name": "Entry Gear",
            "profile": spec.presetProfile,
            "source": "Same MID1 profile (documented placeholder until PreRaids exists for this pin)",
            "warning": "Entry currently aliases MID1 High for this data snapshot.",
        },
    ]


@router.get("/spells/{spell_id}")
def get_spell(spell_id: int) -> dict[str, Any]:
    # Search curated ability catalogs; coefficients stay unverified unless sourced.
    for spec in list_specs():
        for ability in spec.abilities:
            if ability.spellId == spell_id or ability.id == str(spell_id):
                return {
                    "spellId": ability.spellId or spell_id,
                    "name": {"enUS": ability.name, "ruRU": ability.nameRu or ability.name},
                    "owner": {"specKey": spec.key, "specId": spec.id},
                    "simcAction": ability.simcAction,
                    "aoeClass": ability.aoeClass,
                    "cooldown": ability.cooldown,
                    "castTime": ability.castTime,
                    "charges": ability.charges,
                    "provenance": {
                        "status": ability.dataStatus or "implemented",
                        "coefficients": "unverified",
                        "note": "Numeric AP/SP coefficients are not invented; Accurate path uses SimC SpellData",
                    },
                }
    raise HTTPException(status_code=404, detail={"code": "spell_not_found", "message": "Spell not found in catalog"})


@router.get("/items/{item_id}")
def get_item(item_id: int) -> dict[str, Any]:
    return {
        "itemId": item_id,
        "status": "partial",
        "note": "Item DB is seeded via SimC profile gear lines; full item encyclopedia requires DBC ETL.",
        "provenance": {"confidence": "unverified"},
    }


@router.get("/sets/{set_id}")
def get_set(set_id: str) -> dict[str, Any]:
    return {
        "setId": set_id,
        "status": "partial",
        "note": "Tier set bonuses are applied inside SimulationCraft MID profiles when present.",
        "bonuses": {},
        "provenance": {"confidence": "unverified"},
    }


@router.get("/raid-effects")
def raid_effects() -> dict[str, Any]:
    return get_raid_effects()


@router.post("/talents/import", response_model=TalentImportResult)
def talents_import(body: TalentImportRequest) -> TalentImportResult:
    return import_talent_string(body.exportString, body.expectedSpecId)


@router.post("/talents/export")
def talents_export(body: TalentImportRequest) -> dict[str, str]:
    return {"exportString": export_talent_passthrough(body.exportString)}


@router.post("/talents/validate", response_model=TalentImportResult)
def talents_validate(body: TalentImportRequest) -> TalentImportResult:
    return import_talent_string(body.exportString, body.expectedSpecId)


@router.post("/simulations", response_model=SimulationJobView)
def create_simulation(body: SimulationRequest, sync: bool = Query(default=False)) -> SimulationJobView:
    settings = get_settings()
    spec = resolve_spec(spec_id=body.specId, spec_key=body.specKey)
    if spec is None:
        raise HTTPException(status_code=404, detail={"code": "spec_not_found", "message": "Spec not found"})
    body.specId = spec.id
    body.specKey = spec.key

    engine = get_engine_for_request(body, settings)
    validation = engine.validate_request(body, spec)
    if not validation.ok:
        raise HTTPException(
            status_code=400,
            detail={"code": "validation_error", "message": "; ".join(validation.errors)},
        )

    cache_key = simulation_cache_key(
        body,
        simc_commit=settings.data_snapshot_id.split("-")[-1],
        data_snapshot_id=settings.data_snapshot_id,
    )
    cached_id = find_cached_job(cache_key)
    if cached_id:
        session = get_session()
        try:
            cached = session.get(SimulationJobRow, cached_id)
            if cached:
                return _job_view(cached)
        finally:
            session.close()

    job_id = uuid.uuid4().hex
    now = utcnow()
    row = SimulationJobRow(
        id=job_id,
        status=JobStatus.queued.value,
        cache_key=cache_key,
        request_json=body.model_dump_json(),
        result_json=None,
        error=None,
        created_at=now,
        updated_at=now,
    )
    session = get_session()
    try:
        session.add(row)
        session.commit()
    finally:
        session.close()

    # Fast estimate and mock always sync; Accurate may enqueue when worker available.
    if sync or settings.sim_engine.lower() == "mock" or body.fight.mode == SimulationMode.fast_estimate:
        run_simulation_job(job_id)
    else:
        queue = get_queue()
        queue.enqueue(run_simulation_job, job_id, job_id=f"sim-{job_id}", job_timeout=settings.sim_timeout_seconds + 30)

    session = get_session()
    try:
        row = session.get(SimulationJobRow, job_id)
        assert row is not None
        return _job_view(row)
    finally:
        session.close()


@router.get("/simulations/{job_id}", response_model=SimulationJobView)
def get_simulation(job_id: str) -> SimulationJobView:
    session = get_session()
    try:
        row = session.get(SimulationJobRow, job_id)
        if row is None:
            raise HTTPException(status_code=404, detail={"code": "job_not_found", "message": "Job not found"})
        return _job_view(row)
    finally:
        session.close()


@router.get("/simulations/{job_id}/results", response_model=SimulationResult)
def get_simulation_results(job_id: str) -> SimulationResult:
    view = get_simulation(job_id)
    if view.status != JobStatus.succeeded or view.result is None:
        raise HTTPException(
            status_code=409,
            detail={"code": "result_unavailable", "message": f"Job status is {view.status}"},
        )
    return view.result


@router.post("/simulations/{job_id}/cancel")
def cancel_simulation(job_id: str) -> dict[str, Any]:
    session = get_session()
    try:
        row = session.get(SimulationJobRow, job_id)
        if row is None:
            raise HTTPException(status_code=404, detail={"code": "job_not_found", "message": "Job not found"})
        if row.status in {JobStatus.succeeded.value, JobStatus.failed.value}:
            return {"id": job_id, "status": row.status, "cancelled": False}
        row.status = JobStatus.cancelled.value
        row.updated_at = utcnow()
        session.commit()
        try:
            redis: Redis = get_redis()
            job = Job.fetch(f"sim-{job_id}", connection=redis)
            job.cancel()
        except Exception:  # noqa: BLE001
            pass
        return {"id": job_id, "status": JobStatus.cancelled.value, "cancelled": True}
    finally:
        session.close()


@router.post("/compare", response_model=ComparisonResult)
@router.post("/comparisons", response_model=ComparisonResult)
def create_comparison(body: ComparisonRequest) -> ComparisonResult:
    build_a = body.buildA.model_copy(deep=True)
    build_b = body.buildB.model_copy(deep=True)
    build_a.fight = body.fight.model_copy(deep=True)
    build_b.fight = body.fight.model_copy(deep=True)
    build_a.gear = body.gear
    build_b.gear = body.gear
    seed = body.seed if body.seed is not None else 417391
    build_a.seed = seed
    build_b.seed = seed

    spec_a = resolve_spec(spec_id=build_a.specId, spec_key=build_a.specKey)
    spec_b = resolve_spec(spec_id=build_b.specId, spec_key=build_b.specKey)
    if spec_a is None or spec_b is None or spec_a.id != spec_b.id:
        raise HTTPException(
            status_code=400,
            detail={"code": "spec_mismatch", "message": "Comparisons require the same specialization"},
        )

    job_a = create_simulation(build_a, sync=True)
    job_b = create_simulation(build_b, sync=True)
    if job_a.result is None or job_b.result is None:
        raise HTTPException(
            status_code=500,
            detail={"code": "comparison_failed", "message": job_a.error or job_b.error or "Missing results"},
        )

    result = compare_results(
        job_a_id=job_a.id,
        job_b_id=job_b.id,
        result_a=job_a.result,
        result_b=job_b.result,
    )
    result.note = f"{result.note} (paired seed={seed})"

    session = get_session()
    try:
        row = ComparisonRow(
            id=uuid.uuid4().hex,
            payload_json=body.model_dump_json(),
            result_json=result.model_dump_json(),
            created_at=utcnow(),
        )
        session.add(row)
        session.commit()
    finally:
        session.close()

    return result


@router.post("/stat-weights")
def stat_weights(body: StatWeightsRequest) -> dict[str, Any]:
    """Finite-difference weights via Fast Estimate (paired deterministic)."""
    settings = get_settings()
    engine = FastEstimateEngine(settings)
    spec = resolve_spec(spec_id=body.base.specId, spec_key=body.base.specKey)
    if spec is None:
        raise HTTPException(status_code=404, detail={"code": "spec_not_found", "message": "Spec not found"})
    base_req = body.base.model_copy(deep=True)
    base_req.fight.mode = SimulationMode.fast_estimate
    base_result = engine.run(base_req, spec)
    weights: dict[str, float] = {}
    from app.domain.models import CharacterStats

    for stat, delta in body.deltas.items():
        altered = base_req.model_copy(deep=True)
        stats = (altered.gear.customStats or CharacterStats()).model_copy(deep=True)
        altered.gear.customStats = stats
        altered.gear.preset = "custom"
        key = "versatility" if stat in {"vers", "versatility"} else stat
        if key in {"crit", "haste", "mastery", "versatility"}:
            setattr(stats, key, int(delta))
        up = engine.run(altered, spec)
        weights[stat] = (up.meanDps - base_result.meanDps) / max(1, abs(int(delta)))
    return {
        "baseDps": base_result.meanDps,
        "weights": weights,
        "isApproximation": True,
        "note": "Stat weights from Fast Estimate finite differences — not Accurate SimC scale factors",
    }


@router.post("/explain")
def explain(body: ExplainRequest) -> dict[str, Any]:
    result = body.result
    top = sorted(result.breakdown, key=lambda r: r.damage, reverse=True)[:10]
    focus = None
    if body.focusAbility:
        focus = next((r for r in result.breakdown if r.name == body.focusAbility), None)
    return {
        "meanDps": result.meanDps,
        "personalDps": result.personalDps,
        "effectiveDps": result.effectiveDps,
        "isApproximation": result.isApproximation,
        "topAbilities": [r.model_dump(mode="json") for r in top],
        "focus": focus.model_dump(mode="json") if focus else None,
        "assumptions": result.assumptions,
        "warnings": result.warnings,
        "engine": result.engine,
    }


@router.get("/builds", response_model=list[BuildRecord])
def list_builds() -> list[BuildRecord]:
    session = get_session()
    try:
        rows = session.query(BuildRow).order_by(BuildRow.created_at.desc()).limit(100).all()
        return [
            BuildRecord(
                id=r.id,
                name=r.name,
                createdAt=r.created_at.isoformat(),
                request=SimulationRequest.model_validate_json(r.request_json),
            )
            for r in rows
        ]
    finally:
        session.close()


@router.post("/builds", response_model=BuildRecord)
def create_build(payload: dict[str, Any]) -> BuildRecord:
    name = str(payload.get("name") or "Untitled Build")
    request = SimulationRequest.model_validate(payload.get("request") or payload)
    row = BuildRow(
        id=uuid.uuid4().hex,
        name=name,
        request_json=request.model_dump_json(),
        created_at=utcnow(),
    )
    session = get_session()
    try:
        session.add(row)
        session.commit()
        return BuildRecord(
            id=row.id,
            name=row.name,
            createdAt=row.created_at.isoformat(),
            request=request,
        )
    finally:
        session.close()


@router.get("/builds/{build_id}", response_model=BuildRecord)
def get_build(build_id: str) -> BuildRecord:
    session = get_session()
    try:
        row = session.get(BuildRow, build_id)
        if row is None:
            raise HTTPException(status_code=404, detail={"code": "build_not_found", "message": "Build not found"})
        return BuildRecord(
            id=row.id,
            name=row.name,
            createdAt=row.created_at.isoformat(),
            request=SimulationRequest.model_validate_json(row.request_json),
        )
    finally:
        session.close()
