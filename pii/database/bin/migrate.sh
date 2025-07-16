#!/usr/bin/env bash
set -e

# ----- Load environment variables from .env -----
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="$SCRIPT_DIR/../data/.env"
if [ -f "$ENV_FILE" ]; then
  set -o allexport
  source "$ENV_FILE"
  set +o allexport
else
  echo "Warning: .env file not found at $ENV_FILE; using defaults"
fi

# ----- Determine database URL -----
if [ -n "$DATABASE_URL" ]; then
  DB_URL="$DATABASE_URL"
else
  POSTGRES_USER="${POSTGRES_USER:-bariendo}"
  POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-bariendo}"
  POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
  POSTGRES_PORT="${POSTGRES_PORT:-5432}"
  POSTGRES_DB="${POSTGRES_DB:-bariendo}"
  DB_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}"
fi
export DATABASE_URL="$DB_URL"
echo "🔄 Running Alembic migrations against $DATABASE_URL"

# ----- Run Alembic with explicit config path -----
# alembic.ini lives in the 'database' directory
ALEMBIC_CONFIG="$SCRIPT_DIR/../alembic.ini"

# Change to the database directory so migrations find the 'migrations' folder
cd "$SCRIPT_DIR/.."

# Execute migrations
if command -v poetry >/dev/null 2>&1; then
  poetry run alembic -c "$ALEMBIC_CONFIG" upgrade head
else
  alembic -c "$ALEMBIC_CONFIG" upgrade head
fi
