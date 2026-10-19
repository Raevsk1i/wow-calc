# Testing

## Unit (API)

```bash
cd apps/api && python3 -m pytest -q
```

Covers:

- json2 parsing fixture
- APL allowlist / skip_actions
- talent string header decode
- cache key stability
- comparison significance band
- mock API happy path

## Integration (SimulationCraft)

`tests/test_simc_integration.py` runs a real Shadow Priest quick sim when `engine/simc/bin/simc` exists.

## Frontend

```bash
cd apps/web && npm test
```

## E2E

Requires web + API running:

```bash
cd apps/web
npx playwright install chromium
npm run test:e2e
```

Primary scenario (manual / future expansion): class → spec → talents → abilities → 5 targets → Simulate → DPS → compare.

## Regression policy

Do **not** assert exact stochastic DPS equality. Assert:

- process success
- `meanDps > 0`
- breakdown structure present
- optional statistical band around a recorded baseline for the same seed/iterations
