# Testing

## API

```bash
cd apps/api
SIM_ENGINE=mock python3 -m pytest
```

Coverage highlights:

- `test_coverage_registry.py` — 13/40 keys, Arcane/Devourer/Aug, Fast Estimate, ability disable rebuild
- `test_fast_estimate.py` — target scaling
- Existing APL/talent/parser/mock suites

Accurate SimC integration (`test_simc_integration.py`) skips when the binary is absent.

## Smoke (requires SimC binary)

```bash
./engine/simc/build.sh
python3 scripts/smoke_specs.py
```

Runs all `canAccurate` specs against the pin.

## Web

```bash
cd apps/web
npm test
npm run lint
npm run build
```
