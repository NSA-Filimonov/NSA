.PHONY: prod-up prod-down prod-logs prod-ps prod-restart prod-smoke prod-check
prod-up:
	docker compose -f docker-compose.prod.yml up -d --build --remove-orphans
prod-down:
	docker compose -f docker-compose.prod.yml down --remove-orphans
prod-logs:
	docker compose -f docker-compose.prod.yml logs -f --tail=200
prod-ps:
	docker compose -f docker-compose.prod.yml ps
prod-restart:
	docker compose -f docker-compose.prod.yml down --remove-orphans
	docker compose -f docker-compose.prod.yml up -d --build --remove-orphans
prod-smoke:
	API_URL=http://127.0.0.1 ./scripts/smoke_prod.sh
# Быстрая проверка живости API через nginx
prod-check:
	curl -fsS http://127.0.0.1/health && echo "\nOK: API is healthy"
.PHONY: test-integration
test-integration:
	docker compose -f docker-compose.prod.yml up -d --build
	docker compose -f docker-compose.prod.yml run --rm tests
	docker compose -f docker-compose.prod.yml down
.PHONY: ci-test
ci-test:
	docker compose -f docker-compose.prod.yml up -d --build
	docker compose -f docker-compose.prod.yml run --rm tests
	docker compose -f docker-compose.prod.yml down
