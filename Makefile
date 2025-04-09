export DOCKER_DEFAULT_PLATFORM=linux/amd64

up:
	docker compose -f docker-compose-local.yml up -d

rebuild:
	docker compose -f docker-compose-local.yml up --build -d

down:
	docker compose -f docker-compose-local.yml down --remove-orphans

up_ci:
	docker compose -f docker-compose-ci.yml up -d

up_ci_rebuild:
	docker compose -f docker-compose-ci.yml up --build -d

down_ci:
	docker compose -f docker-compose-ci.yml down --remove-orphans