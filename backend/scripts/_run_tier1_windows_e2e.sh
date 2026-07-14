#!/usr/bin/env bash
# Tier 1 Windows E2E: MLX on host + Redis/Postgres in Docker + R2/cache verification
set -euo pipefail
ROOT=/mnt/g/ThunderMarketingCorp/HyerEnrichment
BACKEND="$ROOT/backend"
DOCKER="$BACKEND/docker"
URL='https://www.linkedin.com/in/rajshamani/?isSelfProfile=false'

echo "========== 1) Docker: redis + postgres + api =========="
cd "$DOCKER"
docker compose up -d redis postgres api
docker compose ps redis postgres api

echo ""
echo "========== 2) Windows host: create_session check =========="
cd "$BACKEND"
python scripts/create_session.py check || true

echo ""
echo "========== 3) Windows host: local MLX scrape + R2 + cache =========="
python scripts/local_multilogin_scrape_test.py --linkedin-url "$URL"
SCRAPE_EXIT=$?

echo ""
echo "========== 4) Redis tier1 keys =========="
cd "$DOCKER"
docker compose exec -T redis redis-cli KEYS 'tier1:*' || true
docker compose exec -T redis redis-cli KEYS 'tier1:photo:*' || true

echo ""
echo "========== 5) Postgres photo_cache =========="
docker compose exec -T postgres psql -U hyrepath -d hyrepath -c \
  "SELECT slug, left(asset_url, 80) AS asset_url, extraction_method, confidence FROM photo_cache WHERE slug = 'rajshamani';" \
  2>/dev/null || echo "(photo_cache table missing or postgres unreachable from compose)"

echo ""
echo "========== 6) Cache verify (skip scrape) =========="
cd "$BACKEND"
python scripts/local_multilogin_scrape_test.py --linkedin-url "$URL" --skip-scrape || true

echo ""
echo "========== SUMMARY =========="
echo "local_multilogin_scrape_test exit=$SCRAPE_EXIT"
exit "$SCRAPE_EXIT"
