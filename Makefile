# Delta Plax Education Suite - developer tasks
# Usage: make <target>

BACKEND := backend
PY := python

.PHONY: help install migrate bootstrap seed run test test-unit lint docker-up docker-down

help:
	@echo "Targets:"
	@echo "  install     Install backend dependencies"
	@echo "  migrate     Run Alembic migrations (alembic upgrade head)"
	@echo "  bootstrap   Create the Delta Plax super admin (needs DELTAPLAX_ADMIN_PASSWORD)"
	@echo "  seed        Seed demo data"
	@echo "  run         Run the FastAPI dev server (cloud)"
	@echo "  test        Run the full test suite with pytest (needs deps)"
	@echo "  test-unit   Run the dependency-free 'laws' tests with stdlib unittest"
	@echo "  lint        Ruff lint the backend"
	@echo "  docker-up   Build and start the full stack"
	@echo "  docker-down Stop the stack"

install:
	cd $(BACKEND) && pip install -r requirements.txt

migrate:
	cd $(BACKEND) && alembic upgrade head

bootstrap:
	$(PY) scripts/bootstrap_superadmin.py

seed:
	$(PY) scripts/seed_demo_data.py

run:
	cd $(BACKEND) && uvicorn app.main:app --reload

test:
	cd $(BACKEND) && pytest

# Runs without any third-party dependencies installed.
test-unit:
	cd $(BACKEND) && $(PY) -m unittest discover -s tests -v

lint:
	cd $(BACKEND) && ruff check app tests

docker-up:
	docker compose -f docker/docker-compose.yml up -d --build

docker-down:
	docker compose -f docker/docker-compose.yml down
