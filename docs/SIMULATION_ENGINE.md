# Simulation Engine

## Pin

See [`engine/simc/SIMC_PIN`](../engine/simc/SIMC_PIN).

Current pin:

- Branch: `midnight`
- Commit: `d91a570`
- Version string: `1210-01`
- Game: `12.1.5.70448` (hotfix 2026-10-17)

## Build locally

```bash
./engine/simc/build.sh
./engine/simc/bin/simc packages/game-data/presets/12.1.5/MID1_Priest_Shadow.simc \
  iterations=100 desired_targets=1 max_time=180 threads=2 json2=/tmp/out.json output=/dev/null
```

## Docker

```bash
docker build -f engine/simc/Dockerfile -t wow-dps-lab-simc engine/simc
```

## json2 contract

Parser reads:

- `version`, `git_revision`, `git_branch`
- `sim.players[0].collected_data.dps|dmg|fight_length`
- `sim.players[0].stats[*].actual_amount / portion_amount / num_executes / portion_aps`
- optional `stats_pets`, optional `action_sequence` (diagnostic sample only)

Fixture: `apps/api/tests/fixtures/json2_assassination_excerpt.json`

## Rotation control

- Automatic: omit custom `actions` → SimC default APL
- Disable abilities: `skip_actions=token1/token2` (curated tokens only)
- Custom priority: generated allowlisted `actions=` list
- Custom APL text: allowlisted `actions*` / `skip_actions` only

## Exit / failure handling

Initialization errors that mention talent hashes trigger one retry without `talents=` and with curated `hero_talents=` when available.

## Interpreting DPS

Mean DPS is stochastic. Prefer `mean_std_dev` / confidence style bands. Small deltas inside the error band are not reliable upgrades.
