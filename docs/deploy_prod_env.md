# 生产环境部署指南（ibowdex.cn / 国内本地服务器）

> 域名：`https://ibowdex.cn:8443/` | 机器配置：8C8G | 系统：Ubuntu Server 26.04 LTS | 面板：1Panel + OpenResty
>
> **端口转发**：路由器做端口转发，外网 8060→内网 80 / 外网 8443→内网 443。OpenResty 监听内网 80/443，但 HTTPS 跳转和 error_page 497 必须带外网端口 `:8443`。
>
> **分支说明**：生产环境对应 `main` 分支。测试环境（kimpi.cn）部署请看 [deploy_test_env.md](deploy_test_env.md)。
>
> **前置要求**：ibowdex.cn 已完成 ICP 备案，在执行本指南前请先按 [1panel_checklist.md](1panel_checklist.md) 逐项确认。

---

## 0. 动手前确认清单（速查）

| # | 检查内容 | 怎么查 | 期望结果 |
|---|---------|--------|---------|
| 0 | **ibowdex.cn ICP 备案有效** | https://beian.miit.gov.cn/ → 公共查询 | 能查到备案号 |
| 1 | **1Panel 中 ibowdex.cn 站点已创建** | 1Panel → 网站 → 列表 | 存在 `ibowdex.cn` 条目 |
| 2 | **路由器端口转发已配置** | 路由器管理 → 端口转发/NAT | 外 8060→内 80、外 8443→内 443 |
| 3 | **域名 DNS A 记录指向本服务器公网 IP** | `dig ibowdex.cn +short` | 返回服务器公网 IP |
| 4 | **docker 与 docker compose v2 可用** | `docker --version && docker compose version` | 都有版本号 |
| 5 | **服务器时间已与 NTP 同步** | `timedatectl status` | `System clock synchronized: yes` |

---

## 1. 上传代码到服务器

**方式 A：git clone（推荐）**

```bash
# SSH 登录服务器后执行
cd /opt
# 生产环境拉 main 分支
git clone -b main <你的 Git 仓库地址> openyzj
```

**方式 B：scp 上传**

```bash
# 在本地 PowerShell 执行（替换 <SERVER_IP>）
scp -r "d:\Downloads\.vibeCode\.openYZJ" root@<SERVER_IP>:/opt/openyzj
```

上传完成后，项目根目录应为 `/opt/openyzj`。

---

## 2. 配置 .env

```bash
cd /opt/openyzj
cp .env.example .env
nano .env
```

**必须修改**的字段：

| 字段 | 要求 | 示例 |
|------|------|------|
| `MONGO_PASSWORD` | 任意复杂值，不能保留 `changeme` | `M0ng0_p@ss_prod!` |
| `APP_SECRET_KEY` | ≥32 字符随机串 | `openssl rand -base64 32` 生成 |
| `ADMIN_TOKEN` | 任意复杂值，管理 API 使用 | `myProdAdminToken_2024` |
| `ENV` | 改为 `prod` | `ENV=prod` |

> `ENV=prod` 会开启严格签名验证（不允许跳过），请确保云之家 appSecret 已在 robots 集合中注册后再切换。

**可选字段**：

- `OPENAI_API_KEY`：留空走 AI stub，有 key 才走真实 AI
- `LOG_LEVEL`：生产环境建议 `INFO`（默认）

保存退出。

---

## 3. 启动 Docker 服务

```bash
cd /opt/openyzj

# 使用生产 compose（mongo wiredTiger 缓存 2G，适配 8G 内存）
docker compose -f docker-compose.prod.yml up -d --build
```

等待约 30-60s 镜像构建完成，验证状态：

```bash
docker compose -f docker-compose.prod.yml ps
```

期望所有 service 状态为 `Up (healthy)`：

```
NAME        STATUS
fastapi     Up (healthy)
mongo       Up (healthy)
```

如果 fastapi 状态是 `Up (health: starting)`，再等 30s 后重查——这是正常的冷启动等待期。

---

## 4. 在 1Panel 创建 ibowdex.cn 站点

> 如果已在"确认清单"中确认站点存在，可跳到步骤 5。

1. 打开 1Panel 面板（通常是 `http://<服务器IP>:<面板端口>`）
2. 左侧菜单 → **网站** → 点击 **创建网站**
3. 选择类型：**反向代理**
4. 填写：
   - **主域名**：`ibowdex.cn`
   - **额外域名**：`www.ibowdex.cn`
   - **代理地址**：`http://127.0.0.1:8000`
5. 点击**确认**

站点创建后，1Panel 会自动生成基础 OpenResty 配置。

---

## 5. 申请 SSL 证书（DNS API 方式）

由于端口转发导致 HTTP 80 端口非标准（外网 8060），无法使用 HTTP 方式验证域名，需使用 DNS API 方式获取 Let's Encrypt 证书。

1. 1Panel → 网站 → `ibowdex.cn` → 点击 **HTTPS**
2. 选择证书来源：**申请证书**
3. 验证方式：选择 **DNS API**（非 HTTP）
4. 选择 DNS 服务商并填写 API 凭证（如阿里云 DNS 的 AccessKey）
5. 点击申请，等待验证完成
6. 开启 **强制 HTTPS**（HTTP 自动跳转到 HTTPS）

证书路径（OpenResty 容器内视角，即配置文件中使用的路径）：

```
/www/sites/ibowdex.cn/ssl/fullchain.pem
/www/sites/ibowdex.cn/ssl/privkey.pem
```

> 在宿主机 SSH 中查看时，实际路径为 `/opt/1panel/www/sites/ibowdex.cn/ssl/`。
> OpenResty 运行在 Docker 容器中，宿主机 `/opt/1panel/www/` 挂载到容器内 `/www/`，配置文件中写容器内路径即可。

> 注意：DNS API 方式下，`/.well-known/acme-challenge` 路径非必须，但配置中已保留以备将来切换回 HTTP 验证。

---

## 6. 配置 OpenResty 反向代理（自定义超时）

1Panel 自动生成的反代配置超时值为 60s，需要替换为符合云之家 3s 限制的配置。

**操作路径**：1Panel → 网站 → `ibowdex.cn` → 配置 → 修改配置文件

将配置文件内容**全量替换**为 `nginx/ibowdex.cn.conf` 中的内容：

```bash
# 在服务器上查看配置内容
cat /opt/openyzj/nginx/ibowdex.cn.conf
```

配置文件中的路径已与 1Panel 实际路径一致，无需手动替换。关键注意点：

- **端口 8443**：HTTP→HTTPS 跳转和 error_page 497 必须带 `:8443`，因为外网通过非标准端口访问
- **proxy include 冲突**：1Panel 默认在 `/www/sites/ibowdex.cn/proxy/` 下生成反代配置文件，本配置已将反代规则直接写入 `location /`，**请删除 1Panel 自动生成的 proxy include 文件**，否则会产生冲突

保存后，点击**重载**或执行：

```bash
# 1Panel 管理的 OpenResty，用 docker exec 方式测试配置
docker exec 1panel-openresty openresty -t
docker exec 1panel-openresty openresty -s reload
```

> 注意：1Panel 中 OpenResty 运行在容器内，不能直接在宿主机执行 `nginx -t`。

---

## 7. 自检

```bash
# 绕过 OpenResty 直连 FastAPI（验证应用层是否 OK）
curl http://127.0.0.1:8000/health

# 通过域名访问（走 OpenResty + HTTPS + 端口转发，验证全链路）
curl -fsS https://ibowdex.cn:8443/health
```

两条命令都期望返回：

```json
{"app":"ok","mongo":"ok","env":"prod"}
```

如果第一条通、第二条不通，问题在 OpenResty 配置或端口转发；两条都不通，问题在 FastAPI/Docker。

---

## 8. 模拟 webhook 请求验证签名

```bash
cd /opt/openyzj

# SHA256 签名测试
python3 scripts/gen_test_sign.py --domain https://ibowdex.cn:8443 --robot-code test --algo sha256

# SHA1 签名测试
python3 scripts/gen_test_sign.py --domain https://ibowdex.cn:8443 --robot-code test --algo sha1
```

两种算法都要跑，任意一种返回以下内容即正常：

```json
{"success":true,"data":{"type":2,"content":"你好，我是机器人，已经准备好为你服务~"}}
```

---

## 9. 在云之家后台注册机器人

1. 登录**云之家开发者后台**
2. 创建机器人，消息接收地址填：
   ```
   https://ibowdex.cn:8443/api/yunzhijia/webhook/{robot_code}
   ```
3. 云之家自动测试通过后下发正式 `appSecret`
4. 通过 admin API 注册到 robots 集合：

```bash
curl -X POST https://ibowdex.cn:8443/api/admin/robots \
  -H "Authorization: Bearer <你的 ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"robot_code":"<robot_code>","name":"<机器人名>","appSecret":"<云之家给的 appSecret>"}'
```

5. 云之家分配 `robotId` 后补回：

```bash
curl -X PUT https://ibowdex.cn:8443/api/admin/robots/<robot_code> \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"robotId":"<云之家分配的 robotId>"}'
```

---

## 10. 排查清单

| 现象 | 排查步骤 |
|------|---------|
| `curl /health` 不通 | 1) `docker compose -f docker-compose.prod.yml ps` 看容器状态<br>2) `docker compose -f docker-compose.prod.yml logs fastapi` 看应用日志 |
| HTTPS 不通 | 1) 确认 1Panel 中 SSL 证书未过期<br>2) 确认路由器端口转发 8443→443 生效<br>3) `docker exec 1panel-openresty openresty -t` 检查配置语法 |
| 云之家测试失败 | 1) `docker compose -f docker-compose.prod.yml logs --tail 100 fastapi`<br>2) 关注 `sign verification failed` 或 `cost_ms` 超过 2500 |
| MongoDB 连不上 | `docker compose -f docker-compose.prod.yml logs mongo` 看启动日志 |
| 容器反复重启 | `docker compose -f docker-compose.prod.yml logs --tail 200` 查退出原因 |
| OpenResty 配置报错 | `docker exec 1panel-openresty openresty -t` 查语法错误 |

---

## 附录 A：常用运维命令速查

```bash
# 查看容器状态
docker compose -f docker-compose.prod.yml ps

# 查看 fastapi 实时日志
docker compose -f docker-compose.prod.yml logs -f fastapi

# 查看 mongo 日志
docker compose -f docker-compose.prod.yml logs -f mongo

# 重启所有服务
docker compose -f docker-compose.prod.yml restart

# 仅重启 fastapi
docker compose -f docker-compose.prod.yml restart fastapi

# 重新构建并启动
docker compose -f docker-compose.prod.yml up -d --build

# 停止所有服务
docker compose -f docker-compose.prod.yml down

# 清理未使用的镜像
docker image prune -f

# OpenResty 配置测试 & 重载（1Panel 容器方式）
docker exec 1panel-openresty openresty -t
docker exec 1panel-openresty openresty -s reload
```

## 附录 B：后续更新代码流程

每次生产环境代码更新流程：

```bash
# 1. 本地：功能在 staging 验证通过后，合并到 main
git checkout main
git merge staging
git push origin main

# 2. 服务器：拉取最新代码并重新构建
cd /opt/openyzj
git checkout main
git pull origin main
docker compose -f docker-compose.prod.yml up -d --build
```
