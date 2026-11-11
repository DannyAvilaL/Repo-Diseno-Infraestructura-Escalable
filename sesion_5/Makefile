.PHONY: install test lint run web loadtest experiments
install:
	python3.12 -m venv .venv && . .venv/bin/activate && pip install -r requirements-dev.txt && cd frontend && npm ci
test:
	PYTHONPATH=src pytest -q
lint:
	ruff check . && mypy src
	ruff check . && mypy src
run:
	PYTHONPATH=src uvicorn serverless_llm.main:app --reload --port 8000
web:
	cd frontend && npm run dev
loadtest:
	PYTHONPATH=src python -m loadtest.run_loadtest --help
experiments:
	PYTHONPATH=src python -m experiments.cold_start_experiment
