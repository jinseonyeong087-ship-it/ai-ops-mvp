COMPOSE_FILE=infra/docker-compose.yml
ENV_FILE?=.env

.PHONY: init-env check-env up down logs ps migrate seed restart smoke

init-env:
	@if [ ! -f .env ]; then cp .env.example .env; echo "[ok] .env created from .env.example"; else echo "[skip] .env already exists"; fi

check-env:
	@if [ ! -f $(ENV_FILE) ]; then echo "[error] $(ENV_FILE) not found. run: make init-env"; exit 1; fi

up: check-env
	docker compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) up -d

down: check-env
	docker compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) down

restart: check-env
	docker compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) restart

logs: check-env
	docker compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) logs -f --tail=200

ps: check-env
	docker compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) ps

migrate: check-env
	docker compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) exec backend alembic upgrade head

seed: check-env
	docker compose -f $(COMPOSE_FILE) --env-file $(ENV_FILE) exec -T postgres \
		psql -U $${POSTGRES_USER:-aiops} -d $${POSTGRES_DB:-ai_ops_mvp_dev} \
		< backend/scripts/seed_safe_8k.sql

smoke:
	./backend/scripts/smoke_test.sh
