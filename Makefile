.PHONY: simc api worker web test smoke

simc:
	./engine/simc/build.sh

api:
	cd apps/api && SIM_ENGINE=simc uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

worker:
	cd apps/worker && PYTHONPATH=../api python3 worker.py

web:
	cd apps/web && NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000/api/v1 npm run dev -- --port 3000 --hostname 127.0.0.1

test:
	cd apps/api && SIM_ENGINE=mock pytest -q
	cd apps/web && npm test

smoke:
	python3 scripts/smoke_specs.py
