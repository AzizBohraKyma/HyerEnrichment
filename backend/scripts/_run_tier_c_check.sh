#!/usr/bin/env bash
set -euo pipefail
cd /mnt/g/ThunderMarketingCorp/HyerEnrichment/backend/docker

MULTILOGIN_HOST_IP=$(ip route show default | awk '{print $3}')
export MULTILOGIN_HOST_IP
echo "=== Tier C test ==="
echo "MULTILOGIN_HOST_IP=$MULTILOGIN_HOST_IP"

code=$(curl -sk -o /dev/null -w "%{http_code}" --connect-timeout 5 "https://${MULTILOGIN_HOST_IP}:45001/api/v2/" || true)
echo "host_launcher_probe: HTTP $code"

docker compose -f docker-compose.yml -f docker-compose.tier1.yml up -d worker

echo ""
echo "=== /etc/hosts in worker ==="
docker compose -f docker-compose.yml -f docker-compose.tier1.yml exec -T worker cat /etc/hosts | grep -E 'launcher|host.docker' || true

echo ""
echo "=== inject scripts (excluded from image by .dockerignore) ==="
docker compose -f docker-compose.yml -f docker-compose.tier1.yml exec -T worker mkdir -p /app/backend/scripts
docker compose -f docker-compose.yml -f docker-compose.tier1.yml cp ../scripts/create_session.py worker:/app/backend/scripts/create_session.py
docker compose -f docker-compose.yml -f docker-compose.tier1.yml cp ../scripts/_tier1_setup_common.py worker:/app/backend/scripts/_tier1_setup_common.py

echo ""
echo "=== create_session diagnose (worker) ==="
docker compose -f docker-compose.yml -f docker-compose.tier1.yml exec -T -w /app/backend worker \
  python scripts/create_session.py diagnose

echo ""
echo "=== create_session check (worker) ==="
set +e
docker compose -f docker-compose.yml -f docker-compose.tier1.yml exec -T -w /app/backend worker \
  python scripts/create_session.py check
exit_code=$?
set -e
echo "exit_code=$exit_code"
exit "$exit_code"
