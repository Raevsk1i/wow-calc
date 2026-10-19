# API

Base path: `/api/v1`

## Catalog / ruleset

| Method | Path |
|---|---|
| GET | `/health` |
| GET | `/builds/current` |
| GET | `/game/versions` |
| GET | `/classes` |
| GET | `/classes/{classId}/specs` |
| GET | `/specs` |
| GET | `/specs/{id}` | numeric id **or** canonical key |
| GET | `/specs/{id}/talents` |
| GET | `/specs/{id}/abilities` |
| GET | `/specs/{id}/apl` |
| GET | `/specs/{id}/rotations/default` |
| GET | `/specs/{id}/gear-presets` |
| GET | `/spells/{spellId}` |
| GET | `/items/{itemId}` |
| GET | `/sets/{setId}` |
| GET | `/raid-effects` |

## Talents

| Method | Path |
|---|---|
| POST | `/talents/import` |
| POST | `/talents/export` |
| POST | `/talents/validate` |

## Simulations

| Method | Path | Notes |
|---|---|---|
| POST | `/simulations?sync=` | `fight.mode`: `fast_estimate` \| `quick` \| `accurate` |
| GET | `/simulations/{id}` | |
| GET | `/simulations/{id}/results` | |
| POST | `/simulations/{id}/cancel` | |
| POST | `/compare` | paired seed |
| POST | `/comparisons` | alias |
| POST | `/stat-weights` | Fast Estimate finite differences |
| POST | `/explain` | breakdown attribution |

### Simulation request (JSON)

```json
{
  "gameVersion": "12.1.5",
  "specKey": "demon_hunter_devourer",
  "talents": { "exportString": null, "heroTalent": "annihilator", "useProfileTalents": true },
  "gear": { "preset": "high", "rawSimcProfile": null },
  "rotation": { "mode": "automatic", "disabledActions": [], "priority": [], "customApl": null },
  "fight": {
    "targets": 5,
    "duration": 300,
    "fightStyle": "Patchwerk",
    "mode": "fast_estimate",
    "clusterRadiusYards": 5,
    "raid": { "arcaneIntellect": true, "battleShout": true, "bloodlust": true },
    "allies": { "enabled": false }
  }
}
```

Errors use `{ "detail": { "code", "message" } }`.
