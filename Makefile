.PHONY: setup test run-backend run-frontend seed docker-up docker-down

setup:
	python -m venv .venv
	.venv/bin/pip install -r backend/requirements.txt
	.venv/bin/pip install -r backend/requirements-dev.txt
	cd frontend && npm install

test:
	pytest backend/tests -v

run-backend:
	uvicorn app.main:app --app-dir backend --reload --port 8000

run-frontend:
	cd frontend && npm run dev

seed:
	python infrastructure/scripts/seed_demo.py

train-ml:
	python backend/app/ml/train_model.py

docker-up:
	docker-compose up --build -d

docker-down:
	docker-compose down
