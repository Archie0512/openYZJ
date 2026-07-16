#!/usr/bin/env bash
# 联调工具：把某条已落库的金蝶按票回调（by-invoice）重放转发给 System A。
#
# 依赖：curl、jq
# 前置：export ADMIN_TOKEN=<.env 中的 ADMIN_TOKEN>
#      可选 export PROXY_BASE=https://ibowdex.cn:8443（默认值见下）
#
# 用法：
#   ./replay_to_system_a.sh --serial-no SN20260715001
#   ./replay_to_system_a.sh --bill-no  AR-B01A-2026024703
#   ./replay_to_system_a.sh --id 64d0f0a0f0a0f0a0f0a0f0a0
#   ./replay_to_system_a.sh --serial-no SN123 --target-url http://baodetest.haverise.com:23822/callback/invoiceCallback
#   ./replay_to_system_a.sh --bill-no B1 --client-id systemA
#
# 说明：
#   - 未指定 --target-url / --client-id 时，服务端回退到该回调 matched_client_id
#     对应 proxy_client 的 callback_url。
#   - 同一条可反复执行（可重复重放），服务端累加 forward_attempts。
set -euo pipefail

BASE="${PROXY_BASE:-https://ibowdex.cn:8443}"
: "${ADMIN_TOKEN:?请先 export ADMIN_TOKEN=<你的 ADMIN_TOKEN>}"

SERIAL_NO=""; BILL_NO=""; EVENT_ID=""; TARGET_URL=""; CLIENT_ID=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --serial-no)  SERIAL_NO="$2"; shift 2;;
    --bill-no)    BILL_NO="$2";   shift 2;;
    --id)         EVENT_ID="$2";  shift 2;;
    --target-url) TARGET_URL="$2"; shift 2;;
    --client-id)  CLIENT_ID="$2"; shift 2;;
    -h|--help)    grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0;;
    *) echo "未知参数: $1（用 -h 查看用法）"; exit 1;;
  esac
done

AUTH="Authorization: Bearer ${ADMIN_TOKEN}"

# 1) 若未直接给 event id，按 serial_no / bill_no 查列表取最新一条
if [[ -z "$EVENT_ID" ]]; then
  Q=""
  [[ -n "$SERIAL_NO" ]] && Q="serial_no=${SERIAL_NO}"
  [[ -n "$BILL_NO"   ]] && Q="bill_no=${BILL_NO}"
  if [[ -z "$Q" ]]; then
    echo "需提供 --id 或 --serial-no 或 --bill-no 之一"; exit 1
  fi
  URL="${BASE}/api/admin/callback-events?${Q}&endpoint=by-invoice&limit=1"
  echo ">> 查询: ${URL}"
  LIST=$(curl -fsS -H "${AUTH}" "${URL}")
  EVENT_ID=$(echo "${LIST}" | jq -r '.items[0]._id // empty')
  if [[ -z "${EVENT_ID}" ]]; then
    echo "未找到匹配的 by-invoice 回调记录，返回："; echo "${LIST}"; exit 1
  fi
fi
echo ">> event_id = ${EVENT_ID}"

# 2) 组装 replay body（可选 target_url / client_id）
BODY="{}"
[[ -n "$TARGET_URL" ]] && BODY=$(echo "$BODY" | jq -c --arg u "$TARGET_URL" '. + {target_url:$u}')
[[ -n "$CLIENT_ID"  ]] && BODY=$(echo "$BODY" | jq -c --arg c "$CLIENT_ID"  '. + {client_id:$c}')

# 3) 调用 replay 端点
echo ">> 转发: POST ${BASE}/api/admin/callback-events/${EVENT_ID}/replay  body=${BODY}"
curl -sS -X POST "${BASE}/api/admin/callback-events/${EVENT_ID}/replay" \
     -H "${AUTH}" -H "Content-Type: application/json" \
     --data "${BODY}" | jq .
