# Simulation Engine

## Dual mode

| Mode | Engine | Use |
|---|---|---|
| `fast_estimate` | `FastEstimateEngine` | Interactive UI, talent/ability sweeps, approximation |
| `quick` / `accurate` | SimulationCraft CLI | Monte Carlo Accurate results |

Fast Estimate always returns `isApproximation: true` and an `assumptions` list. Never present it as Monte Carlo.

## Pin

See [`engine/simc/SIMC_PIN`](../engine/simc/SIMC_PIN).

- Branch: `midnight`
- Commit: `d91a570`
- Game: `12.1.5.70448` (hotfix 2026-10-17)

## Fast Estimate model

1. Load per-spec baseline DPS + ability shares from `estimate_baselines.json`.
2. Apply level-90 combat rating conversions + piecewise diminishing returns from `ruleset.json`.
3. Scale shares by ability `aoeClass` and target count (not `damage × N`).
4. Apply discrete raid buff/debuff EV factors.
5. Redistribute shares when abilities are disabled (rotation rebuild, not flat DPS subtraction).
6. Augmentation optionally adds ally-attributed contribution when ally model is enabled.

## Accurate (SimC)

Composer builds a sanitized `.simc` profile from MID presets + UI mutations:

- `desired_targets`, `max_time`, `fight_style`, latency
- Discrete raid toggles (`override.bloodlust`, documented buff flags)
- `skip_actions` / custom priority APL (allowlisted)
- Talent string or `hero_talents=` fallback

json2 parser extracts mean/median/std DPS, breakdown, optional action sequence sample, and 95% CI from `mean_std_dev` when present.

## Comparisons

`POST /compare` uses a shared paired seed to reduce noise between builds.
