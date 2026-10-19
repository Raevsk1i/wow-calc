# Game Data

## Version model

`GameVersion → Class → Specialization → TalentTree / Abilities → SimulationSupport`

Catalog: `packages/game-data/catalog/<version>/catalog.json`  
Presets: `packages/game-data/presets/<version>/*.simc`

Current snapshot key: `12.1.5 + clientBuild 70448 + hotfixDate + simcCommit`  
Example: `12.1.5-70448-2026-10-17-d91a570`

Midnight scope: **13 classes / 40 specializations** (including tanks, healers, Devourer, Augmentation). Each spec has a `canonicalId` (e.g. `demon_hunter_devourer`) plus the numeric Blizzard spec id.

## Sources

| Data | Source | License / terms |
|---|---|---|
| Combat / APL | SimulationCraft | GPL-3.0 |
| Gear presets | SimC `profiles/MID2` (MID1 fallback where MID2 missing) | GPL-3.0 |
| Spec support matrix | Curated against pinned SimC smoke tests | Project |
| Talent loadout strings | Blizzard in-game export (passthrough to SimC) | Player export |
| Future talent tree layout / icons | Blizzard Game Data / Media API | Blizzard API ToU |

**Not used as coefficient sources:** Wowhead scrape, invented spell coefficients, wiki damage tables.

Missing numeric fields must be `unverified` / omitted — never guessed. Specs without a SimC preset stay in the registry as `unsupported` with notes (healers + Augmentation on the current pin).

## Support levels

| Level | Meaning |
|---|---|
| `supported` | Smoke-tested MID2 (or verified) preset + curated abilities |
| `experimental` | Preset present; talent hash may need fallback |
| `partial` | Limited APL/ability coverage; sim may run with warnings |
| `unsupported` | No runnable preset on this pin (still listed in UI) |

## Patch update runbook

1. Update `engine/simc/SIMC_PIN` to a new midnight commit that targets the live build.
2. Rebuild with `./engine/simc/build.sh`.
3. Refresh MID2 presets: `scripts/import_mid2_presets.sh /path/to/simc/profiles/MID2 /path/to/simc/profiles/MID1`.
4. Smoke every non-unsupported spec (`scripts/smoke_specs.py`).
5. Update `catalog.json` support flags / notes / `canonicalId` coverage.
6. Bump `dataSnapshotId` and record sources in results.
7. Re-run API pytest + one Monte Carlo sim per Supported spec.

## Adding a specialization

1. Confirm a working SimC profile on the pin (talent hash must init).
2. Add preset under `packages/game-data/presets/<version>/`.
3. Add catalog entry with `canonicalId`, `simulationSupport`, abilities (`simcAction` tokens), hero trees, `coverage`.
4. Add/adjust ability disable tokens that exist in the default APL.
5. Add an integration or smoke test.

## Mid / Entry gear note

This snapshot aliases Mid/Entry to the High MID2 (or MID1 fallback) profile when PreRaid profiles are unavailable for a spec. The API surfaces an explicit warning — values are not fabricated ilvl curves.
