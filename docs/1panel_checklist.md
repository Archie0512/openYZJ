# 1Panel + OpenResty HTTPS 部署前置检查清单（生产环境）

每次生产环境部署前，按此清单逐项确认。
适用范围：ibowdex.cn / 8C8G 本地服务器 / Ubuntu 26.04 / 1Panel + OpenResty。

> 测试环境（宝塔）对应清单见 [baota_checklist.md](baota_checklist.md)。

---

## 必查项（不通过则部署必失败）

- [ ] **域名已完成 ICP 备案（工信部）**
  ibowdex.cn 已完成备案，此项可视为常驻 OK。如更换域名，重新验证。
  验证方法：https://beian.miit.gov.cn/ → 公共查询 → 能查到备案号。

- [ ] **1Panel 中 ibowdex.cn 站点已创建**
  仅申请了 SSL 证书 ≠ 站点可用。必须在 1Panel → 网站 → 列表中能看到站点条目。

- [ ] **服务器防火墙 / 安全组已放行 443/TCP 和 80/TCP**
  验证方法：服务器管理后台 → 防火墙入方向规则，或：
  ```bash
  # 服务器本地测试
  curl -I http://ibowdex.cn   # 应返回 301 跳转
  curl -I https://ibowdex.cn  # 应返回非 502/504
  ```

- [ ] **域名 DNS A 记录指向本服务器公网 IP**
  验证方法：`dig ibowdex.cn +short`，返回值必须是本服务器公网 IP。

- [ ] **OpenResty 配置语法正确**
  每次修改配置文件后必查：
  ```bash
  docker exec 1panel-openresty openresty -t
  # 期望：syntax is ok / test is successful
  ```

- [ ] **服务器时间已与 NTP 同步**
  签名验签依赖时间戳，时差 > 5 分钟会被云之家过滤。
  验证方法：`timedatectl status` → `System clock synchronized: yes`。
  Ubuntu 26.04 默认启用 systemd-timesyncd，一般自动正常。

---

## 强烈建议项

- [ ] **OpenResty proxy 超时已压紧到云之家 3s 限制以内**
  默认反代配置超时 60s，与云之家 3s 窗口冲突必然超时。
  本项目要求（已在 `nginx/ibowdex.cn.conf` 中配置）：
  ```nginx
  proxy_connect_timeout 2s;
  proxy_send_timeout    2s;
  proxy_read_timeout    2500ms;
  ```
  确认 1Panel 配置文件中这三行存在且未被覆盖。

- [ ] **FastAPI 容器仅监听回环地址**
  `docker-compose.prod.yml` 中 `ports: "127.0.0.1:8000:8000"`，不是 `0.0.0.0:8000:8000`。
  防止外网绕过 OpenResty 直连容器。

- [ ] **mongo 容器不映射端口到宿主机**
  `docker-compose.prod.yml` 中 mongo 服务无 `ports` 配置，仅在 docker 内部网络可达。

- [ ] **容器日志已限额**
  `docker-compose.prod.yml` 中每个 service 已配置 `logging: json-file max-size:10m max-file:3`，沿用即可。

- [ ] **`.env` 已替换所有占位值**
  `MONGO_PASSWORD` / `APP_SECRET_KEY` / `ADMIN_TOKEN` 不能保留 `.env.example` 中的默认值。
  `ENV=prod` 开启严格签名验证，确保 robots 集合中已有正式 appSecret。

- [ ] **1Panel 中 OpenResty 日志切割已启用**
  长时间运行日志会很大。1Panel → 网站 → 设置 → 日志切割 → 启用。

---

## 与宝塔版本的关键差异

| 项目 | 宝塔（测试环境） | 1Panel（生产环境） |
|---|---|---|
| 面板端口 | 8888 | 1Panel 自定义端口 |
| OpenResty/Nginx 容器名 | 宿主机直接运行 | `1panel-openresty` |
| 配置语法测试 | `nginx -t`（宿主机） | `docker exec 1panel-openresty openresty -t` |
| 配置重载 | `nginx -s reload` | `docker exec 1panel-openresty openresty -s reload` |
| SSL 证书路径 | `/www/server/panel/vhost/cert/` | `/opt/1panel/apps/openresty/openresty/conf/ssl/` |
| 访问日志路径 | `/www/wwwlogs/` | `/opt/1panel/apps/openresty/openresty/log/` |
| swap 需求 | 必须开启（4G 内存兜底） | 8G 内存充裕，可不开 |

---

## 验收闭环（部署完成后）

- [ ] `curl http://127.0.0.1:8000/health` 返回 `{"app":"ok","mongo":"ok","env":"prod"}`
- [ ] `curl -fsS https://ibowdex.cn/health` 同上（验证 OpenResty 全链路）
- [ ] 浏览器访问 `https://ibowdex.cn` 证书锁显示合法
- [ ] `docker exec 1panel-openresty openresty -t` 输出 `syntax is ok`
- [ ] `docker compose -f docker-compose.prod.yml ps` 所有 service 状态为 `Up (healthy)`
