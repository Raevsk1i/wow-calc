from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from redis import Redis
from rq.job import Job

from app.config import get_settings
from app.data.catalog import get_class, get_spec, list_classes, list_versions
from app.domain.cache_keys import simulation_cache_key
from app.domain.comparison import compare_results
from app.domain.models import (
    BuildRecord,
    ComparisonRequest,
    ComparisonResult,
    JobStatus,
    SimulationJobView,
    SimulationRequest,
    SimulationResult,
    TalentImportRequest,
    TalentImportResult,
)
from app.domain.talents import export_talent_passthrough, import_talent_string
from app.jobs.queue import get_queue, get_redis
from app.jobs.tasks import find_cached_job, run_simulation_job
from app.persistence.db import BuildRow, ComparisonRow, SimulationJobRow, get_session, utcnow
from app.simulation.factory import get_engine

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


@router.get("/health")
def health() -> dict[str, Any]:
    settings = get_settings()
    engine = get_engine(settings)
    return {
        "ok": True,
        "app": settings.app_name,
        "gameVersion": settings.game_version,
        "engine": engine.name,
        "dataSnapshotId": settings.data_snapshot_id,
    }


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


@router.get("/specs/{spec_id}")
def spec_detail(spec_id: int) -> dict[str, Any]:
    spec = get_spec(spec_id)
    if spec is None:
        raise HTTPException(status_code=404, detail={"code": "spec_not_found", "message": "Spec not found"})
    return spec.model_dump(mode="json")


@router.get("/specs/{spec_id}/talents")
def spec_talents(spec_id: int) -> dict[str, Any]:
    spec = get_spec(spec_id)
    if spec is None:
        raise HTTPException(status_code=404, detail={"code": "spec_not_found", "message": "Spec not found"})
    return {
        "specId": spec.id,
        "heroTalentTrees": [h.model_dump(mode="json") for h in spec.heroTalentTrees],
        "talentTree": spec.talentTree.model_dump(mode="json"),
        "notes": (
            "Full interactive node graph requires Blizzard Game Data API snapshot sync. "
            "MVP supports hero talent selection + Blizzard talent string import for SimC."
        ),
    }


@router.get("/specs/{spec_id}/abilities")
def spec_abilities(spec_id: int) -> list[dict[str, Any]]:
    spec = get_spec(spec_id)
    if spec is None:
        raise HTTPException(status_code=404, detail={"code": "spec_not_found", "message": "Spec not found"})
    return [a.model_dump(mode="json") for a in spec.abilities]


@router.get("/specs/{spec_id}/rotations/default")
def spec_default_rotation(spec_id: int) -> dict[str, Any]:
    spec = get_spec(spec_id)
    if spec is None:
        raise HTTPException(status_code=404, detail={"code": "spec_not_found", "message": "Spec not found"})
    actions = [a.simcAction for a in spec.abilities if a.category.value in {"active", "required"}]
    return {
        "specId": spec.id,
        "mode": "automatic",
        "actions": actions,
        "source": "curated catalog + SimulationCraft default APL at runtime",
    }


@router.get("/specs/{spec_id}/gear-presets")
def spec_gear_presets(spec_id: int) -> list[dict[str, Any]]:
    spec = get_spec(spec_id)
    if spec is None:
        raise HTTPException(status_code=404, detail={"code": "spec_not_found", "message": "Spec not found"})
    if not spec.presetProfile:
        return []
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
    spec = get_spec(body.specId)
    if spec is None:
        raise HTTPException(status_code=404, detail={"code": "spec_not_found", "message": "Spec not found"})

    engine = get_engine(settings)
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

    if sync or settings.sim_engine.lower() == "mock":
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


@router.post("/comparisons", response_model=ComparisonResult)
def create_comparison(body: ComparisonRequest) -> ComparisonResult:
    # Force shared fight/gear onto both builds
    build_a = body.buildA.model_copy(deep=True)
    build_b = body.buildB.model_copy(deep=True)
    build_a.fight = body.fight
    build_b.fight = body.fight
    build_a.gear = body.gear
    build_b.gear = body.gear
    if build_a.specId != build_b.specId:
        raise HTTPException(
            status_code=400,
            detail={"code": "spec_mismatch", "message": "Comparisons require the same specId"},
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
