#!/usr/bin/env bash
set -e

# Load environment variables from .env in the data folder (if present)
ENV_FILE="$(dirname "$0")/../data/.env"
if [ -f "$ENV_FILE" ]; then
  set -o allexport
  source "$ENV_FILE"
  set +o allexport
else
  echo "Warning: .env file not found at $ENV_FILE; using defaults"
fi

# Defaults if .env is missing
PGDATA_VOLUME="${PGDATA_VOLUME:-pgdata}"
CONTAINER_NAME="${CONTAINER_NAME:-bariendo_db}"
POSTGRES_IMAGE="${POSTGRES_IMAGE:-postgres:15}"

echo "🔍 Looking for container '$CONTAINER_NAME'..."
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
  echo "🛑 Stopping container '$CONTAINER_NAME'..."
  docker stop "$CONTAINER_NAME" || true

  echo "🗑️  Removing container '$CONTAINER_NAME'..."
  docker rm "$CONTAINER_NAME" || true
else
  echo "⚠️  Container '$CONTAINER_NAME' not found."
fi

echo "🔍 Checking for volume '$PGDATA_VOLUME'..."
if docker volume ls --format '{{.Name}}' | grep -q "^${PGDATA_VOLUME}$"; then
  echo "🗑️  Removing volume '$PGDATA_VOLUME'..."
  docker volume rm "$PGDATA_VOLUME"
else
  echo "⚠️  Volume '$PGDATA_VOLUME' not found."
fi

echo "🔍 Checking for image '$POSTGRES_IMAGE'..."
if docker images --format '{{.Repository}}:{{.Tag}}' | grep -q "^${POSTGRES_IMAGE}$"; then
  echo "🗑️  Removing image '$POSTGRES_IMAGE'..."
  docker image rm "$POSTGRES_IMAGE" || true
else
  echo "⚠️  Image '$POSTGRES_IMAGE' not found in local cache."
fi

echo "✅ All done. Docker container, volume, and image for your database have been purged."
