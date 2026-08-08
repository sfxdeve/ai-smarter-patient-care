.PHONY: fetch-data install test eval up down dev-api dev-web

fetch-data:
	bash scripts/fetch-data.sh

install:
	python3 -m venv backend/.venv
	. backend/.venv/bin/activate && pip install -r backend/requirements.txt
	cd frontend && pnpm install

test:
	. backend/.venv/bin/activate && cd backend && PYTHONPATH=. pytest -q

eval:
	. backend/.venv/bin/activate && cd backend && PYTHONPATH=. python eval/harness.py

eval-offline:
	. backend/.venv/bin/activate && cd backend && PYTHONPATH=. python eval/harness.py --skip-llm

dev-api:
	. backend/.venv/bin/activate && cd backend && PYTHONPATH=. uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-web:
	cd frontend && pnpm dev --host 0.0.0.0 --port 5173

up: fetch-data
	docker compose up --build

down:
	docker compose down
