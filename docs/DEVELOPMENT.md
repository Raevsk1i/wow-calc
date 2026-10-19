# Development

## Repository layout

```text
apps/web          Next.js UI
apps/api          FastAPI application
apps/worker       RQ worker entrypoint
engine/simc       SimC pin, Dockerfile, build script
packages/game-data  versioned catalog + presets
docs              architecture & runbooks
scripts           maintenance utilities
```

## Environment variables

| Variable | Default | Meaning |
|---|---|---|
| `SIM_ENGINE` | `simc` | `simc` or `mock` |
| `SIMC_PATH` | `engine/simc/bin/simc` | CLI binary |
| `SIMC_PROFILES_DIR` | `packages/game-data/presets/12.1.5` | presets |
| `GAME_DATA_DIR` | `packages/game-data` | catalog root |
| `REDIS_URL` | `redis://127.0.0.1:6379/0` | RQ |
| `DATABASE_URL` | sqlite under `apps/api/.data` | persistence |
| `NEXT_PUBLIC_API_BASE` | `http://127.0.0.1:8000/api/v1` | web → api |

## Common workflows

### UI against mock engine

```bash
SIM_ENGINE=mock uvicorn app.main:app --app-dir apps/api --reload --port 8000
cd apps/web && NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000/api/v1 npm run dev
```

### Real sim (sync)

```bash
curl -s -X POST 'http://127.0.0.1:8000/api/v1/simulations?sync=true' \
  -H 'content-type: application/json' \
  -d '{"specId":258,"fight":{"targets":1,"duration":120,"mode":"quick","iterations":20}}'
```

### Custom rotation disable

Send `rotation.disabledActions: ["power_infusion"]` — composed as `skip_actions=power_infusion`.
