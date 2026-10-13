.PHONY: help install test backend frontend mock loadtest deck clean

LAB := labs/00-local-ollama

help:
	@echo "make install   - crea .venv e instala dependencias del laboratorio local"
	@echo "make test      - ejecuta las pruebas del backend y de las herramientas del caso"
	@echo "make backend   - inicia el backend en 127.0.0.1:8000"
	@echo "make frontend  - inicia el frontend en 127.0.0.1:5173"
	@echo "make mock      - inicia el simulador de Ollama (contingencia)"
	@echo "make loadtest  - prueba de carga de la Demo 4"
	@echo "make deck      - regenera la presentación .pptx (requiere pptxgenjs)"

install:
	python3.12 -m venv .venv && . .venv/bin/activate && pip install -r $(LAB)/backend/requirements-dev.txt

test:
	cd $(LAB)/backend && ../../../.venv/bin/pytest -q
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

clean:
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
	rm -rf $(LAB)/frontend/node_modules $(LAB)/frontend/dist
