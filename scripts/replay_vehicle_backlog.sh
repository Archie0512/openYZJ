#!/usr/bin/env bash
# 机动车回调积压批量补转发（replay）。
#
# 前提：转发器机动车适配已部署（docker compose -f docker-compose.prod.yml up -d --build proxy）。
# 原理：找出机动车积压回调 _id，逐条调用 admin replay 接口把发票数据补推给 System A。
#       replay 接口会用 matched_client_id(BD_EAS850) 的 callback_url 作为转发目标。
#
# 在生产宿主机 /opt/openyzj 下运行：
#   bash scripts/replay_vehicle_backlog.sh --dry-run   # 只列出待补转发的 _id，不实际转发
#   bash scripts/replay_vehicle_backlog.sh             # 实际逐条 replay
set -euo pipefail

MONGO_CT="${MONGO_CT:-openyzj-mongo-1}"
PROXY_CT="${PROXY_CT:-openyzj-proxy-1}"
JS_LOCAL="scripts/list_vehicle_backlog.js"

echo "== 查询机动车积压回调 =="
docker cp "$JS_LOCAL" "$MONGO_CT:/tmp/list_vehicle_backlog.js"
IDS=$(docker exec "$MONGO_CT" bash -c 'mongosh "mongodb://$MONGO_INITDB_ROOT_USERNAME:$MONGO_INITDB_ROOT_PASSWORD@localhost:27017/yunzhijia?authSource=admin" --quiet --file /tmp/list_vehicle_backlog.js')

COUNT=$(printf '%s\n' "$IDS" | grep -c . || true)
echo "待补转发：$COUNT 条"
[ "$COUNT" -eq 0 ] && { echo "无积压，退出。"; exit 0; }

if [ "${1:-}" = "--dry-run" ]; then
  printf '%s\n' "$IDS"
  echo "(dry-run：仅列出，未转发)"
  exit 0
fi

OK=0
FAIL=0
while IFS= read -r ID; do
  [ -z "$ID" ] && continue
  RESP=$(docker exec "$PROXY_CT" sh -c "curl -s -X POST http://localhost:8001/api/admin/callback-events/$ID/replay -H \"Authorization: Bearer \$ADMIN_TOKEN\"")
  echo "[$ID] $RESP"
  case "$RESP" in
    *'"forwarded":true'*|*'"forwarded": true'*) OK=$((OK + 1)) ;;
    *) FAIL=$((FAIL + 1)) ;;
  esac
  sleep 0.2
done <<< "$IDS"

echo "== 完成：成功 $OK / 失败 $FAIL =="
