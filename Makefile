bl: # build for local
	docker compose build

migrate: # fails if container is not running
	docker compose run --rm fastapi alembic upgrade head

up:
	docker compose up -d

test:
	docker-compose run --rm fastapi sh -c "\
		black app && \
		ruff app && \
		mypy app && \
		pytest app"

clean:
	docker rm -f $$(docker ps -aq)
	docker volume rm -f $$(docker volume ls -qf dangling=true)
	docker rmi -f $$(docker images -aq)