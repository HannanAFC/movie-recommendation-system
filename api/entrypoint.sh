#!/bin/sh
set -e

mkdir -p data/db data/datasets data/models

echo "Running database migrations..."
uv run flask db upgrade
echo "Starting backend ..."
uv run flask run -h 0.0.0.0 -p 8000