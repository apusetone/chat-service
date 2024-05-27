bl: # build for local
	docker compose build

migrate: # fails if container is not running
	docker compose run --rm fastapi alembic upgrade head

up:
	docker compose up -d

fmt:
	docker compose run --rm fastapi sh -c "\
		ruff format app"

check:
	docker compose run --rm fastapi sh -c "\
		ruff check app && \
		mypy app"

test:
	docker compose run --rm fastapi sh -c "\
		APP_CONFIG_FILE=test pytest app -vv"

clean:
	docker rm -f $$(docker ps -aq)
	docker volume rm -f $$(docker volume ls -qf dangling=true)
	docker rmi -f $$(docker images -aq)

schemaspy:
	docker run --rm -v "$$PWD/docs:/output" \
	--network="container:postgresql" \
	schemaspy/schemaspy \
	-t pgsql11  \
	-host postgresql -port 5432 -db chat_service \
	-s public -u postgres -p postgres \
	-connprops useSSL\\=false \
	-imageformat svg \
	-all -noads
