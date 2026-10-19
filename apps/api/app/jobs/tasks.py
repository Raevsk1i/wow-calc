from __future__ import annotations

import json

from app.data.catalog import get_spec
from app.domain.models import JobStatus, SimulationRequest
from app.persistence.db import SimulationJobRow, get_session, utcnow
from app.simulation.factory import get_engine


def run_simulation_job(job_id: str) -> None:
    session = get_session()
    try:
        row = session.get(SimulationJobRow, job_id)
        if row is None:
            return
        if row.status == JobStatus.cancelled.value:
            return

        row.status = JobStatus.running.value
        row.updated_at = utcnow()
        session.commit()

        request = SimulationRequest.model_validate_json(row.request_json)
        spec = get_spec(request.specId)
        if spec is None:
            row.status = JobStatus.failed.value
            row.error = f"Unknown specId {request.specId}"
            row.updated_at = utcnow()
            session.commit()
            return

        engine = get_engine()
        try:
            result = engine.run(request, spec)
            row.status = JobStatus.succeeded.value
            row.result_json = result.model_dump_json()
            row.error = None
        except Exception as exc:  # noqa: BLE001 - persist failure for API clients
            row.status = JobStatus.failed.value
            row.error = str(exc)
        row.updated_at = utcnow()
        session.commit()
    finally:
        session.close()


def find_cached_job(cache_key: str) -> str | None:
    session = get_session()
    try:
        row = (
            session.query(SimulationJobRow)
            .filter(
                SimulationJobRow.cache_key == cache_key,
                SimulationJobRow.status == JobStatus.succeeded.value,
            )
            .order_by(SimulationJobRow.created_at.desc())
            .first()
        )
        return row.id if row else None
    finally:
        session.close()


def dump_request(request: SimulationRequest) -> str:
    return json.dumps(request.model_dump(mode="json"), sort_keys=True)
