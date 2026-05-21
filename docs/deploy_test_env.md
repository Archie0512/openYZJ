# 测试环境部署指南（kimpi.cn / 阿里云 ECS Ubuntu 22.04）

> 本文档面向**对服务端不太熟悉的同学**，逐步骤引导完成云之家机器人后台的测试环境部署。
> 域名：`https://kimpi.cn/` | 机器配置：2C4G | 系统已装 git、docker、python3、Nginx（宝塔）
>
> **分支说明**：测试环境对应 `staging` 分支。生产环境（ibowdex.cn）部署请看 [deploy_prod_env.md](deploy_prod_env.md)。

---

## 0. 动手前 60 秒确认清单

> **这四项务必在做任何操作前逐条确认**，否则后续步骤会卡住。

| # | 检查内容 | 怎么查 | 期望结果 |
|---|---------|--------|---------|
| 0 | **域名已完成 ICP 备案** | 访问 https://beian.miit.gov.cn/ → 公共查询 → 输入域名 | 能查到备案号。**未备案域名会被云之家等企业平台立即拒绝**，参见下方"ICP 备案未通过的解决路径" |
| 1 | 宝塔面板"网站"列表中是否已存在 `kimpi.cn` 站点 | 登录宝塔面板 → 网站 → 查看列表 | 存在 `kimpi.cn`。**仅签发了 SSL 证书 ≠ 站点已创建**，如果列表里没有，请先跳到"步骤 3"创建 |
| 2 | 阿里云安全组是否已放行 443 和 80 | 阿里云控制台 → ECS → 实例详情 → 安全组 → 入方向规则 | 能看到 `443/443 TCP 0.0.0.0/0 允许` 和 `80/80 TCP 0.0.0.0/0 允许` |
| 3 | docker 与 docker compose 是否可用 | SSH 上去跑 `docker --version` 和 `docker compose version` | 都有版本号输出 |
| 4 | 域名 DNS 是否解析到 ECS 公网 IP | `dig kimpi.cn +short` 或 `nslookup kimpi.cn` | 返回你 ECS 的公网 IP |

### ICP 备案未通过的解决路径

> 如果你的域名（如 kimpi.cn）未完成 ICP 备案，云之家后台会在填入消息接收地址时**立即报错"消息接收地址错误"**，且不会有任何请求到达你的服务器（Nginx 日志无记录）。

**路径 A（推荐长期）：为域名补办 ICP 备案**
1. 登录阿里云控制台 → 搜索"ICP备案" → 进入备案管理
2. 按向导填写主体信息（企业/个人）、网站信息（kimpi.cn）、服务器信息（ECS 实例）
3. 上传证件、提交管局审核，耗时约 1-2 周
4. 阿里云备案入口：https://beian.aliyun.com/

**路径 B（最快）：使用已备案域名**
1. 用你或公司名下已完成备案的域名，解析一个子域名（如 `bot.已备案域名.com`）到 ECS 公网 IP
2. 在宝塔面板为该子域名创建站点 + 申请 SSL 证书
3. 反代配置与 kimpi.cn 完全一致（copy nginx/kimpi.cn.conf 改域名即可）
4. 在云之家后台填入 `https://bot.已备案域名.com/api/yunzhijia/webhook/{robot_code}`

**路径 C（临时过渡）：阿里云函数计算转发**
1. 创建一个阿里云函数计算 HTTP 触发器，把请求原样转发到 ECS 公网 IP:8000
2. 云之家后台填函数计算自带的 HTTPS 地址（*.cn-hangzhou.fc.aliyuncs.com 已备案）
3. 缺点：多一跳延迟约 50-200ms，3s 窗口变紧

---

## 1. 上传代码到 ECS

选一种方式即可：

**方式 A：git clone（推荐）**
```bash
# SSH 登录 ECS 后执行
cd /opt
# 测试环境拉 staging 分支
git clone -b staging <你的 Git 仓库地址> openyzj
```

**方式 B：scp 上传**
```bash
# 在本地 PowerShell 执行（替换 <ECS_IP> 为你的公网 IP）
scp -r "d:\Downloads\.vibeCode\.openYZJ" root@<ECS_IP>:/opt/openyzj
```

上传完成后，ECS 上的项目根目录应为 `/opt/openyzj`。

---

## 2. 配置 .env

```bash
cd /opt/openyzj
cp .env.example .env
nano .env          # 也可以用 vim / vi
```

**必须修改**的字段（不改会被 deploy.sh 拒绝部署）：

| 字段 | 要求 | 示例 |
|------|------|------|
| `MONGO_PASSWORD` | 任意复杂值，不能保留 `changeme` | `M0ng0_p@ss_2024!` |
| `APP_SECRET_KEY` | ≥32 字符随机串 | 用命令生成：`openssl rand -base64 32` |
| `ADMIN_TOKEN` | 任意复杂值，后续管理 API 使用 | `mySecureAdminToken_2024` |
| `ENV` | 改为 `test` | `ENV=test` |

**可选字段**：
- `OPENAI_API_KEY`：留空即走 AI stub（先跑通链路再接 AI）
- `LOG_LEVEL`：测试阶段建议改为 `DEBUG`

保存退出。

---

## 3. 在宝塔面板创建 kimpi.cn 站点

> 如果你在"步骤 0"确认清单中已看到站点存在，可跳到步骤 4。

1. 打开宝塔面板（通常是 `http://<ECS_IP>:8888`）
2. 左侧菜单 → **网站** → 点击 **添加站点**
3. 填写：
   - **域名**：`kimpi.cn`（回车后再加一行 `www.kimpi.cn`）
   - **根目录**：保持默认（`/www/wwwroot/kimpi.cn`）即可，我们用反向代理不需要真实文件
   - **PHP 版本**：选「纯静态」或「不使用」
   - **数据库**：不创建
4. 点击**提交**
5. 回到站点列表 → 找到 `kimpi.cn` → 点击 **设置**
6. 切到 **SSL** 标签 → 选择「已有证书」→ 选中 `kimpi.cn` 的证书 → 点击**保存** → 开启**强制 HTTPS**
7. **验证**：浏览器访问 `https://kimpi.cn`，看到 503 或宝塔默认页面就说明 Nginx + SSL 已经 OK（后端还没起，所以报错正常）

---

## 4. 配置反向代理到 FastAPI

有两种方式，推荐方式 A：

### 方式 A：用 nginx/kimpi.cn.conf 全量替换（推荐）

1. 宝塔面板 → 网站 → `kimpi.cn` → 设置 → **配置文件**
2. 全选当前内容并删除
3. 打开项目中的 `nginx/kimpi.cn.conf` 文件，将全部内容复制粘贴进去
4. **注意证书路径**：确认宝塔面板 SSL 标签显示的证书路径与配置文件中一致
   - 常见路径：`/www/server/panel/vhost/cert/kimpi.cn/fullchain.pem`
   - 如果不一致，按宝塔实际路径替换配置中的 `ssl_certificate` 和 `ssl_certificate_key`
5. 点击**保存**

### 方式 B：通过宝塔图形界面加反向代理

1. 宝塔面板 → 网站 → `kimpi.cn` → 设置 → **反向代理** → 添加
   - 代理名称：`fastapi_upstream`
   - 目标 URL：`http://127.0.0.1:8000`
2. 保存后，**还需手动修改超时值**：
   - 切到配置文件标签
   - 找到 `location / { ... }` 段
   - 添加或修改以下行（因为宝塔默认 60s，超过云之家 3s 限制）：
     ```nginx
     proxy_connect_timeout 2s;
     proxy_send_timeout    2s;
     proxy_read_timeout    2500ms;
     ```
   - 保存

### 验证 Nginx 配置

```bash
# 在 ECS 上执行
nginx -t
# 期望：syntax is ok / test is successful

# 重载
nginx -s reload
```

---

## 5. 启动服务

```bash
cd /opt/openyzj

# 赋予脚本可执行权限
chmod +x scripts/*.sh

# 执行一键部署
./scripts/deploy.sh
```

deploy.sh 会自动完成：拉代码 → 检查 .env → 构建 Docker 镜像 → 启动容器 → 等待健康检查 → 输出结果。

如果看到以下输出说明启动成功：
```
==> health 已通过（用时约 10s）
==> 自检 health 接口
{"app":"ok","mongo":"ok","env":"test"}
==> 部署完成
```

---

## 6. 自检

```bash
# 通过域名访问（走 Nginx + HTTPS）
curl -fsS https://kimpi.cn/health
```

期望返回：
```json
{"app":"ok","mongo":"ok","env":"test"}
```

如果这里不通，先排查：
- `curl http://127.0.0.1:8000/health` 能否直接通（绕过 Nginx）
- 如果直接也不通 → 看容器日志：`docker compose -f docker-compose.prod.yml logs fastapi`
- 如果直接通但域名不通 → 看 Nginx 配置和证书（详见步骤 10 排查清单）

---

## 7. 用模拟测试请求验证 webhook

```bash
cd /opt/openyzj

# SHA256 签名测试
python3 scripts/gen_test_sign.py --domain https://kimpi.cn --robot-code test --algo sha256
# 复制输出的 curl 命令执行
```

期望返回：
```json
{"success":true,"data":{"type":2,"content":"你好，我是机器人，已经准备好为你服务~"}}
```

**两种算法都要跑一遍**——把 `--algo` 换成 `sha1` 再执行一次，确认双路径都能通过：
```bash
python3 scripts/gen_test_sign.py --domain https://kimpi.cn --robot-code test --algo sha1
```

> **关于签名期望值**：`gen_test_sign.py` 会同时输出 SHA256 和 SHA1 的签名值，以及与文档第 7 章期望值的比对结果。如果 SHA1 签名显示「不匹配」但 webhook 仍返回 success，说明我们的验签逻辑走的是 SHA256 通道——这是正常的，只要有一条通道验签成功即可。

---

## 8. 在云之家后台触发真实测试

1. 登录**云之家开发者后台**
2. 创建机器人，消息接收地址填：
   ```
   https://kimpi.cn/api/yunzhijia/webhook/{robot_code}
   ```
   其中 `{robot_code}` 是你为这只机器人起的代号（例如 `reminder`、`kimpi_bot` 等），全英文小写

3. 提交后云之家会自动发起测试请求 → 我们后台会用 `test-secret` 验签并返回欢迎语 → 测试通过后云之家会下发**正式 appSecret**

4. 把云之家给的正式 `appSecret` 通过 admin API 注册到 robots 集合：
   ```bash
   curl -X POST https://kimpi.cn/api/admin/robots \
     -H "Authorization: Bearer <你的 ADMIN_TOKEN>" \
     -H "Content-Type: application/json" \
     -d '{"robot_code":"<robot_code>","name":"<机器人名>","appSecret":"<云之家给的 appSecret>"}'
   ```

5. 等云之家分配 `robotId` 后再补回（也可以等第一次真实消息从日志里看到 robotId 后再补）：
   ```bash
   curl -X PUT https://kimpi.cn/api/admin/robots/<robot_code> \
     -H "Authorization: Bearer <ADMIN_TOKEN>" \
     -H "Content-Type: application/json" \
     -d '{"robotId":"<云之家分配的 robotId>"}'
   ```

---

## 9. 群里 @ 机器人验证

在企业群里 @ 你刚创建的机器人，测试以下场景：

| 发送内容 | 预期响应 |
|---------|---------|
| `你好` | 回显「收到：你好」 |
| `/api foo` | 回执外部 API 调用结果（同步） |
| `/ai 你好` | 立刻回「正在思考中…」，AI 实际回复在 `command_logs` 集合中可查（v1 暂未推回群） |

---

## 10. 排查清单

| 现象 | 排查步骤 |
|------|---------|
| `curl /health` 不通 | 1) `docker compose -f docker-compose.prod.yml ps` 看容器是否 running/healthy<br>2) `docker compose -f docker-compose.prod.yml logs fastapi` 看应用日志 |
| HTTPS 不通 | 1) 浏览器 F12 → Security 标签看 SSL 错误详情<br>2) 宝塔面板 → SSL 确认证书未过期<br>3) 阿里云安全组 443 是否放行 |
| 云之家测试失败 | 1) `docker compose -f docker-compose.prod.yml logs --tail 100 fastapi` 关注 `sign verification failed` 的算法信息<br>2) 检查 3s 超时：关注日志中 `cost_ms` 字段<br>3) 对比回包 content 字符串与日志中的 content 是否一致 |
| MongoDB 连不上 | 1) `docker compose -f docker-compose.prod.yml logs mongo` 看 mongo 容器日志<br>2) 确认 `.env` 中 `MONGO_USER`/`MONGO_PASSWORD` 与 docker compose 一致 |
| 容器反复重启 | 1) `docker compose -f docker-compose.prod.yml logs --tail 200` 看退出原因<br>2) `free -h` 查内存是否 OOM（2C4G 机器跑 mongo7 需要至少 1.5G 可用） |
| 域名解析不到 IP | `dig kimpi.cn +short` 确认 A 记录指向 ECS 公网 IP |

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

# 清理未使用的镜像（释放磁盘）
docker image prune -f

# Nginx 配置测试 & 重载
nginx -t && nginx -s reload
```

## 附录 B：后续更新代码流程

每次代码更新后，只需在 ECS 上执行：
```bash
cd /opt/openyzj
# 确保在 staging 分支上
git checkout staging
git pull origin staging
docker compose -f docker-compose.prod.yml up -d --build
```

> 如果使用了 deploy.sh 脚本，脚本会自动拉取最新代码、构建、重启并自检。
