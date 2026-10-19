# API

Base path: `/api/v1`

## Catalog

| Method | Path |
|---|---|
| GET | `/health` |
| GET | `/game/versions` |
| GET | `/classes` |
| GET | `/classes/{classId}/specs` |
| GET | `/specs/{specId}` |
| GET | `/specs/{specId}/talents` |
| GET | `/specs/{specId}/abilities` |
| GET | `/specs/{specId}/rotations/default` |
| GET | `/specs/{specId}/gear-presets` |

## Talents

| Method | Path | Body |
|---|---|---|
| POST | `/talents/import` | `{ exportString, expectedSpecId? }` |
| POST | `/talents/export` | `{ exportString }` |
| POST | `/talents/validate` | `{ exportString, expectedSpecId? }` |

## Simulations

| Method | Path | Notes |
|---|---|---|
| POST | `/simulations?sync=false` | enqueue RQ job; `sync=true` runs inline |
| GET | `/simulations/{id}` | job status + optional result |
| GET | `/simulations/{id}/results` | 409 unless succeeded |
| POST | `/simulations/{id}/cancel` | best-effort |

### Simulation request (JSON)

```json
{
  "gameVersion": "12.1.5",
  "specId": 258,
  "talents": { "exportString": null, "heroTalent": "archon", "useProfileTalents": true },
  "gear": { "preset": "high", "rawSimcProfile": null },
  "rotation": { "mode": "automatic", "disabledActions": ["power_infusion"], "priority": [], "customApl": null },
  "fight": { "targets": 1, "duration": 180, "fightStyle": "Patchwerk", "mode": "quick", "latencyMs": 50 }
}
```

## Comparisons & builds

| Method | Path |
|---|---|
| POST | `/comparisons` |
| GET/POST | `/builds` |
| GET | `/builds/{id}` |

Errors use `{ "detail": { "code", "message" } }`.
