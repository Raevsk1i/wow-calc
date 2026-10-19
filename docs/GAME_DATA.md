# Game Data

## Version model

`GameVersion → Class → Specialization → TalentTree / Abilities → Readiness`

Catalog: `packages/game-data/catalog/<version>/catalog.json`  
Ruleset: `packages/game-data/catalog/<version>/ruleset.json`  
Presets: `packages/game-data/presets/<version>/*.simc`  
Estimate baselines: `packages/game-data/catalog/<version>/estimate_baselines.json`  
Talent stubs: `packages/game-data/catalog/<version>/talent_stubs.json`  
Raid effects: `packages/game-data/catalog/<version>/raid_effects.json`

Rebuild registry:

```bash
python3 scripts/build_spec_registry.py
```

## Coverage

Exactly **13 classes / 40 character specializations** (canonical keys such as `mage_arcane`, `demon_hunter_devourer`). Hunter pet specs are not counted.

## Readiness

| Status | Meaning |
|---|---|
| `verified` | Smoke-ready MID preset + curated abilities + tests |
| `implemented` | Working MID preset on pin; UI complete |
| `partial` | In registry/UI; Accurate may be unavailable or thin |
| `unsupported` | No Accurate path on this pin |

Every specialization remains visible in API/UI. Missing coefficients are marked unverified — never invented.

## Snapshot fields

`patch`, `clientBuild`, `hotfixDate`, `dataRevision`, `region`, `source`, `verifiedAt`, `confidence`, `aplRevision`

Current pin baseline: **12.1.5.70448**, hotfix **2026-10-17**, SimC `d91a570` (midnight).

## Sources

| Data | Source |
|---|---|
| Accurate combat / APL | SimulationCraft (GPL-3.0) |
| Gear presets | SimC `profiles/MID1` |
| Fast Estimate baselines | Curated shares anchored to MID-style profiles |
| Talent loadout strings | Blizzard in-game export (passthrough to SimC) |
| Talent UI stubs | Curated metadata (not full Blizzard trait graphs) |

**Not used as coefficient sources:** invented spell coefficients, scraped tooltip damage tables without validation.

## Patch update runbook

1. Update `engine/simc/SIMC_PIN`.
2. Rebuild SimC: `./engine/simc/build.sh`.
3. Refresh presets: `scripts/import_mid1_presets.sh`.
4. Rebuild catalog: `python3 scripts/build_spec_registry.py`.
5. Smoke Accurate specs: `scripts/smoke_specs.py`.
6. Bump `ruleset.json` / `dataRevision` / estimate baselines as needed.
7. Re-run API pytest + web tests.
