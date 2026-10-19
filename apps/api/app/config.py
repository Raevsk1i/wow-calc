from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "WoW DPS Lab"
    api_prefix: str = "/api/v1"
    game_version: str = "12.1.5"
    data_snapshot_id: str = "midnight-12.1.5-eu-2026-10-17-d91a570"

    sim_engine: str = "simc"  # simc | mock
    simc_path: str = str(REPO_ROOT / "engine" / "simc" / "bin" / "simc")
    simc_profiles_dir: str = str(REPO_ROOT / "packages" / "game-data" / "presets" / "12.1.5")
    game_data_dir: str = str(REPO_ROOT / "packages" / "game-data")

    redis_url: str = "redis://127.0.0.1:6379/0"
    database_url: str = f"sqlite:///{REPO_ROOT / 'apps' / 'api' / '.data' / 'wow_dps_lab.db'}"

    # Resource limits
    max_iterations_quick: int = 100
    max_iterations_accurate: int = 3000
    max_targets: int = 20
    min_fight_duration: int = 30
    max_fight_duration: int = 600
    sim_timeout_seconds: int = 180
    simc_threads: int = 2
    worker_queue: str = "simulations"

    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
