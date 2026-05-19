#!/usr/bin/env bash
# 一键部署脚本（在 ECS 上执行）
# 首次使用请赋予可执行权限：chmod +x scripts/deploy.sh
# 使用：cd /opt/openyzj && ./scripts/deploy.sh
# 可通过环境变量覆盖：
#   REPO_DIR=/opt/openyzj   仓库目录
#   COMPOSE_FILE=docker-compose.prod.yml  生产 compose 文件
#   GIT_BRANCH=main         拉取分支
set -euo pipefail

# ========== 配置区 ==========
REPO_DIR="${REPO_DIR:-/opt/openyzj}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
# GIT_BRANCH="${GIT_BRANCH:-main}"
# ===========================

cd "$REPO_DIR"

echo "==> 当前目录: $(pwd)"
echo "==> 使用 compose 文件: $COMPOSE_FILE"

# echo "==> 拉取最新代码（branch=$GIT_BRANCH）未使用git直接宝塔面板传输的数据"
# git fetch --all
# git reset --hard "origin/$GIT_BRANCH"

echo "==> 检查 .env 是否存在"
if [ ! -f .env ]; then
  echo "ERROR: .env 不存在，请先 cp .env.example .env 并修改 MONGO_PASSWORD / APP_SECRET_KEY / ADMIN_TOKEN 后重试"
  exit 1
fi

# 简单兜底：阻止使用 .env.example 默认占位值上线
if grep -qE '^(MONGO_PASSWORD=changeme|APP_SECRET_KEY=please-change-this|ADMIN_TOKEN=admin-bearer-token-changeme)' .env; then
  echo "ERROR: .env 仍包含 .env.example 默认占位值，请修改后再部署"
  exit 1
fi

echo "==> 构建镜像"
docker compose -f "$COMPOSE_FILE" build

echo "==> 滚动重启服务"
docker compose -f "$COMPOSE_FILE" up -d

echo "==> 等待健康检查（最多 60s）"
for i in $(seq 1 12); do
  sleep 5
  if curl -fsS http://127.0.0.1:8000/health >/dev/null 2>&1; then
    echo "==> health 已通过（用时约 $((i*5))s）"
    break
  fi
  echo "    ... 第 ${i} 次重试"
done

echo "==> 容器状态"
docker compose -f "$COMPOSE_FILE" ps

echo "==> 自检 health 接口"
curl -fsS http://127.0.0.1:8000/health && echo

echo "==> 部署完成。如需通过域名验证：curl -fsS https://kimpi.cn/health"
