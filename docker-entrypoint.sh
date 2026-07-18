#!/bin/bash
set -e
set -o pipefail

CONTAINER_ID="${HOSTNAME:-unknown}"

log_info() {
    echo "[INFO] [${CONTAINER_ID}] $(date -u +"%Y-%m-%dT%H:%M:%SZ") $1"
}

log_error() {
    echo "[ERROR] [${CONTAINER_ID}] $(date -u +"%Y-%m-%dT%H:%M:%SZ") $1" >&2
}

log_info "Container startup initiated (ID: ${CONTAINER_ID})"
log_info "Waiting for database to be ready..."
start_time=$(date +%s)

PYTHON_BIN="${VIRTUAL_ENV:-/app/.venv}/bin/python"

if "${PYTHON_BIN}" <<'PY'
import sys
import time

from sqlalchemy import create_engine, text

from lrn.config import Config

config = Config()
max_attempts = 30

for attempt in range(1, max_attempts + 1):
    try:
        engine = create_engine(config.db_url, connect_args={"connect_timeout": 5})
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        sys.exit(0)
    except Exception as e:
        if attempt >= max_attempts:
            print(f"Connection failed: {e}", file=sys.stderr)
            sys.exit(1)
        time.sleep(2)
PY
then
  wait_duration=$(( $(date +%s) - start_time ))
  log_info "Database is ready! (waited ${wait_duration}s)"
else
  log_error "Database connection failed after 30 attempts"
  exit 1
fi

# Schema is created by the app lifespan (SQLModel metadata.create_all).
log_info "Starting application server..."
exec "$@"
