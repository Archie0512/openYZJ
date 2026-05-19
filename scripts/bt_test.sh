#!/usr/bin/env bash
# 部署后联调自检脚本
# 使用：bash scripts/bt_test.sh
# 可通过环境变量覆盖：
#   DOMAIN=https://kimpi.cn  目标域名
#   ROBOT_CODE=test          路径中的 robot_code（必须与 admin API 注册的一致）
set -euo pipefail

DOMAIN="${DOMAIN:-https://kimpi.cn}"
ROBOT_CODE="${ROBOT_CODE:-test}"

echo "============================================================"
echo " 测试目标: $DOMAIN  robot_code=$ROBOT_CODE"
echo "============================================================"

echo
echo "==> 1) 健康检查"
curl -fsS "$DOMAIN/health" && echo

echo
echo "==> 2) 生成测试签名（SHA256）并打 webhook"
python3 scripts/gen_test_sign.py --domain "$DOMAIN" --robot-code "$ROBOT_CODE" --algo sha256 \
  | tee /tmp/yzj_curl_sha256.sh
echo
echo "（如需直接执行 SHA256 版本：bash /tmp/yzj_curl_sha256.sh）"

echo
echo "==> 3) 生成测试签名（SHA1）并打 webhook"
python3 scripts/gen_test_sign.py --domain "$DOMAIN" --robot-code "$ROBOT_CODE" --algo sha1 \
  | tee /tmp/yzj_curl_sha1.sh
echo
echo "（如需直接执行 SHA1 版本：bash /tmp/yzj_curl_sha1.sh）"

echo
echo "==> 4) 列出最近 5 条消息（请在 ECS 上以下命令手动执行，需替换 \$MONGO_USER / \$MONGO_PASSWORD）"
cat <<'EOF'
docker compose -f docker-compose.prod.yml exec mongo \
  mongosh -u "$MONGO_USER" -p "$MONGO_PASSWORD" --authenticationDatabase admin yunzhijia \
  --eval 'db.messages.find().sort({received_at:-1}).limit(5).pretty()'
EOF

echo
echo "==> 5) 查看 fastapi 最近 50 行日志"
echo "docker compose -f docker-compose.prod.yml logs --tail 50 fastapi"

echo
echo "==> 自检脚本执行完毕。下一步：在云之家开发者后台填入 $DOMAIN/api/yunzhijia/webhook/<robot_code> 触发真实测试"
