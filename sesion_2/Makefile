.PHONY: help install test backend frontend mock loadtest deck regiones gateway frontend2 failover deck2 test-cloud clean

LAB := labs/00-local-ollama
LAB2 := labs/01-local-gateway

help:
	@echo "make install   - crea .venv e instala dependencias del laboratorio local"
	@echo "make test      - ejecuta las pruebas del backend y de las herramientas del caso"
	@echo "make backend   - inicia el backend en 127.0.0.1:8000"
	@echo "make frontend  - inicia el frontend en 127.0.0.1:5173"
	@echo "make mock      - inicia el simulador de Ollama (contingencia)"
	@echo "make loadtest  - prueba de carga de la Demo 4"
	@echo "make deck      - regenera la presentación .pptx (requiere pptxgenjs)"
	@echo "--- Sesión 2 ---"
	@echo "make regiones  - inicia las dos regiones simuladas (9001 y 9002) en segundo plano"
	@echo "make gateway   - inicia el gateway multi-región en 127.0.0.1:8080"
	@echo "make frontend2 - inicia el frontend de LOC-02 en 127.0.0.1:5173"
	@echo "make failover  - Demo 2: prueba de conmutación bajo carga"
	@echo "make deck2     - regenera la presentación de la Sesión 2"
	@echo "make test-cloud - pruebas sin red de AZ-G, GCP-D y AWS-E (un entorno por laboratorio)"

install:
	python3.12 -m venv .venv && . .venv/bin/activate && pip install -r $(LAB)/backend/requirements-dev.txt

test:
	cd $(LAB)/backend && ../../../.venv/bin/pytest -q
	cd $(LAB2)/backend && ../../../.venv/bin/pytest -q
	.venv/bin/pytest -q labs/common/tests

backend:
	cd $(LAB)/backend && ../../../.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --env-file ../.env

frontend:
	cd $(LAB)/frontend && npm install && npm run dev

mock:
	.venv/bin/python $(LAB)/scripts/mock_ollama.py --port 11434 --batch 2

loadtest:
	.venv/bin/python $(LAB)/load-tests/loadtest.py --levels 1 2 4 8 --requests 8

deck:
	cd sesiones/s01-arquitecturas-base/slides && node build_deck.js

regiones:
	.venv/bin/python $(LAB2)/scripts/mock_region.py --name region-a --port 9001 &
	.venv/bin/python $(LAB2)/scripts/mock_region.py --name region-b --port 9002 &

gateway:
	cd $(LAB2)/backend && ../../../.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8080 --env-file ../.env

frontend2:
	cd $(LAB2)/frontend && npm install && npm run dev

failover:
	.venv/bin/python $(LAB2)/load-tests/failover_test.py --duracion 40 --falla-en 10 --recupera-en 25

deck2:
	cd sesiones/s02-topologias/slides && node build_deck.js

test-cloud:
	for d in labs/21-azure-topologias labs/11-gcp-topologias labs/31-aws-topologias; do \
	  (cd $$d && python3.12 -m venv .venv && .venv/bin/pip install -q -r requirements-dev.txt && .venv/bin/pytest -q) || exit 1; \
	done

clean:
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
	rm -rf $(LAB)/frontend/node_modules $(LAB)/frontend/dist $(LAB2)/frontend/node_modules $(LAB2)/frontend/dist
	rm -rf $(LAB2)/data/batches
