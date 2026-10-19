# API

Base path: `/api/v1`

## Catalog

| Method | Path |
|---|---|
| GET | `/health` |
| GET | `/builds/current` |
| GET | `/raid-effects` |
| GET | `/game/versions` |
| GET | `/classes` |
| GET | `/classes/{classId}/specs` |
| GET | `/specs/{specId}` |
| GET | `/specs/{specId}/talents` |
| GET | `/specs/{specId}/abilities` |
| GET | `/specs/{specId}/rotations/default` |
| GET | `/specs/{specId}/gear-presets` |

`/health` and `/builds/current` expose pinned ruleset metadata: patch `12.1.5`, `clientBuild` 70448, hotfix date, `dataSnapshotId`, and 13/40 class-spec coverage.

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
| POST | `/stat-weights` | 501 stub |
| POST | `/explain` | 501 stub |

### Simulation request (JSON)

```json
{
  "gameVersion": "12.1.5",
  "specId": 258,
  "talents": { "exportString": null, "heroTalent": "archon", "useProfileTalents": true },
  "gear": { "preset": "high", "rawSimcProfile": null },
  "rotation": { "mode": "automatic", "disabledActions": ["power_infusion"], "priority": [], "customApl": null },
  "fight": {
    "targets": 5,
    "duration": 300,
    "fightStyle": "Patchwerk",
    "mode": "preview",
    "clusterRadiusYards": 5,
    "latencyMs": 50,
    "iterations": null
  },
  "raid": {
    "arcaneIntellect": true,
    "battleShout": true,
    "markOfTheWild": true,
    "skyfury": true,
    "chaosBrand": true,
    "mysticTouch": true,
    "bloodlust": { "enabled": true, "atMs": 0 }
  },
  "incomingDamageModel": { "enabled": true, "attacksPerSecond": 1.2, "physicalFraction": 0.75, "magicFraction": 0.25 },
  "healerDamageProfile": { "damageActivity": 1.0, "healingActivity": 0.0 },
  "party": { "enabled": false, "members": [] },
  "seed": null
}
```

Fight `mode`: `preview` | `monte_carlo` (aliases `quick` | `accurate` still accepted).

Result extras: `p05Dps`, `p95Dps`, `dpsPerTarget`, `personalDps`, `externalContributionDps`, `effectiveDps`, `assumptions[]`.

## Comparisons & builds

| Method | Path |
|---|---|
| POST | `/comparisons` |
| GET/POST | `/builds` |
| GET | `/builds/{id}` |

Errors use `{ "detail": { "code", "message" } }`.
