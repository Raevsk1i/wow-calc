# Game Data

## Version model

`GameVersion → Class → Specialization → TalentTree / Abilities → SimulationSupport`

Catalog: `packages/game-data/catalog/<version>/catalog.json`  
Presets: `packages/game-data/presets/<version>/*.simc`

## Sources

| Data | Source | License / terms |
|---|---|---|
| Combat / APL | SimulationCraft | GPL-3.0 |
| Gear presets | SimC `profiles/MID1` | GPL-3.0 |
| Spec support matrix | Curated against pinned SimC smoke tests | Project |
| Talent loadout strings | Blizzard in-game export (passthrough to SimC) | Player export |
| Future talent tree layout / icons | Blizzard Game Data / Media API | Blizzard API ToU |

**Not used as coefficient sources:** Wowhead scrape, invented spell coefficients, wiki damage tables.

## Patch update runbook

1. Update `engine/simc/SIMC_PIN` to a new midnight commit that targets the live build.
2. Rebuild with `./engine/simc/build.sh`.
3. Refresh MID1 (or successor) presets: `scripts/import_mid1_presets.sh`.
4. Smoke every Supported spec (`scripts/smoke_specs.py`).
5. Update `catalog.json` support flags / notes.
6. Bump `dataSnapshotId` and record sources in results.
7. Re-run API pytest + one Accurate sim per Supported spec.

## Adding a specialization

1. Confirm a working SimC profile on the pin (talent hash must init).
2. Add preset under `packages/game-data/presets/<version>/`.
3. Add catalog entry with `simulationSupport`, abilities (`simcAction` tokens), hero trees.
4. Add/adjust ability disable tokens that exist in the default APL.
5. Add an integration or smoke test.

## Mid / Entry gear note

This snapshot aliases Mid/Entry to MID1 High when PreRaid profiles are unavailable for a spec. The API surfaces an explicit warning — values are not fabricated ilvl curves.
