# 宝塔 + 阿里云 HTTPS 部署前置检查清单

每次基于宝塔的 HTTPS 部署，都按此清单逐项打勾后再动手。

适用范围：所有基于宝塔面板 + 阿里云 ECS 的 HTTPS 反向代理部署任务（来源：项目内沉淀的「宝塔HTTPS部署前置检查决策」经验）。

---

## 必查项（不通过则部署必失败）

- [ ] **域名已完成 ICP 备案（工信部）**
  云之家等企业级 SaaS 平台在接受 webhook 地址前会校验域名备案状态，未备案域名会被**立即拒绝**且不触发任何到你服务器的请求。
  验证方法：访问 https://beian.miit.gov.cn/ → 公共查询 → 输入域名 → 能查到备案号即通过。
  如果未备案：参见项目 docs/deploy_test_env.md 中的解决路径（已备案域名替换 / 阿里云 ICP 备案申请）。

- [ ] **宝塔面板"网站"列表中目标域名站点已创建**
  仅签发证书 ≠ 站点可用。证书只是证书库里的一项资源，必须绑定到具体站点才能在 443 端口生效。
  验证方法：宝塔面板 → 网站 → 列表里看到目标域名条目。

- [ ] **阿里云安全组已放行 443/TCP 入方向**
  推荐同时放行 80/TCP 用于 HTTP→HTTPS 跳转。
  验证方法：阿里云控制台 → ECS → 实例 → 安全组 → 入方向规则中能看到 `443/443 TCP 0.0.0.0/0 允许` 与 `80/80 TCP 0.0.0.0/0 允许`。

- [ ] **域名 DNS A 记录指向当前 ECS 公网 IP**
  验证方法：`dig <domain> +short` 或 `nslookup <domain>`，返回值必须是当前 ECS 公网 IP。
  如果近期更换过机器或 IP，注意 DNS TTL 缓存（一般 10 分钟～1 小时）。

- [ ] **ECS 时间已与 NTP 同步**
  签名验签依赖时间戳，时差 > 5 分钟可能被云之家反爬过滤直接拒绝。
  验证方法：`timedatectl status` 看到 `System clock synchronized: yes`。
  Ubuntu 22.04 默认启用 systemd-timesyncd，一般不用手动配置。

---

## 强烈建议项（不影响部署，但事故风险高）

- [ ] **宝塔面板已开启面板 SSL**
  自身管理面板使用 HTTPS（默认 8888 端口），避免凭据明文传输。
  路径：宝塔面板 → 面板设置 → 面板 SSL。

- [ ] **ECS 已启用 swap**
  2C4G 机器同时跑 mongo + fastapi 时内存抖动，没有 swap 容易 OOM-killer 直接干掉容器。
  验证方法：`free -h` 看 Swap 行 total > 0。
  开启 2G swap：
  ```bash
  fallocate -l 2G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
  ```

- [ ] **容器日志已限额**
  json-file driver 默认无上限，长时间运行会把磁盘打满。
  在 docker-compose 中为每个 service 加：
  ```yaml
  logging:
    driver: "json-file"
    options:
      max-size: "10m"
      max-file: "3"
  ```
  本项目已在 `docker-compose.prod.yml` 中配置，沿用即可。

- [ ] **宝塔已开启日志切割**
  `/www/wwwlogs/<domain>.access.log` 长时间运行同样会很大。
  路径：宝塔面板 → 网站 → 设置 → 日志切割 → 启用。

- [ ] **`.env` 已替换所有占位值**
  `MONGO_PASSWORD` / `APP_SECRET_KEY` / `ADMIN_TOKEN` 任何一个保留 `.env.example` 里的默认值都是高危。
  本项目 `scripts/deploy.sh` 已加 grep 兜底，但建议在 review 阶段就消除占位。

---

## Nginx 反代专属检查（业务相关）

- [ ] **proxy_*_timeout 已压紧到云之家 3s 限制以内**
  默认值（60s）+ 云之家 3s 硬窗口 = 100% 超时失败。
  本项目要求：`proxy_connect_timeout 2s; proxy_send_timeout 2s; proxy_read_timeout 2500ms;`

- [ ] **fastapi 容器仅监听回环地址**
  `127.0.0.1:8000:8000`，不是 `0.0.0.0:8000:8000`。
  目的：防止绕过 Nginx 直连容器，外网无法访问 8000。

- [ ] **mongo 容器不映射端口到宿主机**
  仅在 docker 内部网络可达，外网完全不可见。

---

## 验收闭环（部署完成后）

- [ ] `curl -fsS https://<domain>/health` 返回 200 且 `mongo:"ok"`
- [ ] 浏览器访问 `https://<domain>` 证书锁是合法的（不是 Let's Encrypt 自签或过期警告）
- [ ] `nginx -t` 输出 `syntax is ok / test is successful`
- [ ] `docker compose ps` 所有 service 状态都是 `Up (healthy)`
