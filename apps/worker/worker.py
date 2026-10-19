#!/usr/bin/env python3
"""RQ worker entrypoint for WoW DPS Lab simulations."""

from __future__ import annotations

import sys
from pathlib import Path

# Allow importing the API package when launched from repo root / apps/worker
API_ROOT = Path(__file__).resolve().parents[1] / "api"
sys.path.insert(0, str(API_ROOT))

from redis import Redis  # noqa: E402
from rq import Worker  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.persistence.db import init_db  # noqa: E402


def main() -> None:
    settings = get_settings()
    init_db()
    redis = Redis.from_url(settings.redis_url)
    worker = Worker([settings.worker_queue], connection=redis)
    worker.work(with_scheduler=False)


if __name__ == "__main__":
    main()
