from __future__ import annotations

import hashlib
import json

from app.domain.models import SimulationRequest


def canonical_request_dict(request: SimulationRequest) -> dict:
    payload = request.model_dump(mode="json")
    return payload


def simulation_cache_key(
    request: SimulationRequest,
    *,
    simc_commit: str,
    data_snapshot_id: str,
) -> str:
    blob = {
        "request": canonical_request_dict(request),
        "simcCommit": simc_commit,
        "dataSnapshotId": data_snapshot_id,
    }
    raw = json.dumps(blob, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
