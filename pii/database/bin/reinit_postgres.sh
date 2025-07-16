#!/bin/bash
docker compose -f "$(dirname "$0")/../docker-compose.yml" down -v
docker volume rm pgdata
docker volume create pgdata
docker compose -f "$(dirname "$0")/../docker-compose.yml" up -d