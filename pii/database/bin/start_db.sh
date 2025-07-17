#!/usr/bin/env bash
set -e

# Load environment variables from .env in the data folder (if present)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="$SCRIPT_DIR/../data/.env"
if [ -f "$ENV_FILE" ]; then
  set -o allexport
  source "$ENV_FILE"
  set +o allexport
else
  echo "Warning: .env file not found at $ENV_FILE; using defaults"
fi

# Set defaults if not provided via env
PGDATA_VOLUME="${PGDATA_VOLUME:-prenuvo_pii_pgdata}"
CONTAINER_NAME="${CONTAINER_NAME:-prenuvo_pii_db}"
POSTGRES_USER="${POSTGRES_USER:-prenuvo_pii_user}"

echo "Using volume: $PGDATA_VOLUME"

# Ensure Docker volume exists
if ! docker volume ls --format '{{.Name}}' | grep -q "^${PGDATA_VOLUME}$"; then
  echo "Creating Docker volume '$PGDATA_VOLUME'..."
  docker volume create "$PGDATA_VOLUME"
else
  echo "Docker volume '$PGDATA_VOLUME' already exists."
fi

# Determine docker-compose command to use
DC_CMD="${DOCKER_COMPOSE_CMD:-docker-compose}"

# Compose file setup
data_dir="$SCRIPT_DIR/../data"
compose_file="$data_dir/docker-compose.yml"
backup_file="${compose_file}.bak"

if [ ! -f "$backup_file" ]; then
  echo "Backing up original compose file to $backup_file"
  cp "$compose_file" "$backup_file"
fi

# Rebuild docker-compose.yml with external volume declaration
awk '/^volumes:/ {exit} {print}' "$backup_file" > "$compose_file"

cat <<EOF >> "$compose_file"
volumes:
  $PGDATA_VOLUME:
    external: true
EOF

# Start the container
echo "Starting Postgres container using '$DC_CMD'..."
pushd "$data_dir" >/dev/null
$DC_CMD up -d
popd >/dev/null

# Wait for Postgres to become available
echo "Waiting for Postgres to be available…"
until docker exec "$CONTAINER_NAME" pg_isready -U "$POSTGRES_USER" > /dev/null 2>&1; do
  sleep 1
  echo "Waiting for database to be ready..."
done

echo "Postgres is up, running migrations and seed…"
bash "$SCRIPT_DIR/migrate.sh"
# bash "$SCRIPT_DIR/seed_db.sh"
