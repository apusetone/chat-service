# builder
FROM python:3.12 AS export

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock ./
RUN poetry export -o /requirements.lock \
    && poetry export --with dev -o /requirements-dev.lock

FROM python:3.12 AS builder
COPY --from=export /requirements.lock ./
RUN pip install --no-cache-dir -r ./requirements.lock

FROM python:3.12 AS dev-builder
COPY --from=export /requirements-dev.lock ./
RUN pip install --no-cache-dir -r ./requirements-dev.lock

# base
FROM python:3.12-slim AS base
WORKDIR /fastapi

RUN apt-get update \
    && apt-get -y install libpq5 graphviz \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -U pip setuptools wheel

EXPOSE 8000
ENV APP_CONFIG_FILE=local
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--reload", "--reload-dir", "app"]

# local
FROM base AS local

COPY --from=dev-builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=dev-builder /usr/local/bin /usr/local/bin

# prod
FROM base AS prod

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY ./src/ /fastapi/
