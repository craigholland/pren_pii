#!/bin/bash
docker compose -f "$(dirname "$0")/../docker-compose.yml" down -v
docker volume rm $PGDATA_VOLUME
docker volume create $PGDATA_VOLUME
docker compose -f "$(dirname "$0")/../docker-compose.yml" up -d