# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.13

# -----------------------------------------------------------------------------
# Stage 1: resolve dependencies with Poetry into /app/.venv
# -----------------------------------------------------------------------------
FROM python:${PYTHON_VERSION}-trixie AS builder

ENV POETRY_VERSION=2.3.2 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR=/tmp/poetry-cache \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}"

WORKDIR /app

COPY pyproject.toml poetry.lock README.md ./
COPY lrn ./lrn

RUN poetry install --without dev --no-ansi


FROM python:${PYTHON_VERSION}-slim-trixie AS prod

WORKDIR /app
ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

RUN groupadd -r appuser && useradd --create-home -r -g appuser appuser

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/lrn /app/lrn

COPY --chown=appuser:appuser docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# Pre-compile bytecode at image build time to reduce import CPU on container start.
RUN python -m compileall -q -j 0 /app/lrn /app/.venv

RUN find /app -path /app/.venv -prune -o -exec chown appuser:appuser {} + && \
    find /app -path /app/.venv -prune -o -exec chmod 755 {} +

USER appuser

EXPOSE 8080

ENTRYPOINT ["/app/docker-entrypoint.sh"]

CMD ["fastapi", "run", "lrn/main.py", "--port", "80"]
