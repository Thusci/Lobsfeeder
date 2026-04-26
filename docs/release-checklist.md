# Release Checklist

发布前请按下面顺序确认。这里的重点是避免把配置页面、密钥或旧依赖带到生产环境里。

## 1. Dependency And Test Gate

```bash
python -m venv /tmp/lobsfeeder-release-venv
/tmp/lobsfeeder-release-venv/bin/python -m pip install --upgrade pip
/tmp/lobsfeeder-release-venv/bin/python -m pip install -r requirements.txt
/tmp/lobsfeeder-release-venv/bin/python -m pytest -q
```

还应运行：

```bash
python -m compileall -q app
git diff --check
```

## 2. Required Runtime Secrets

生产环境至少设置：

```bash
export ROUTER_API_KEY=...
export ADMIN_API_KEY=...
export MODEL_A_API_KEY=...
export MODEL_B_API_KEY=...
export MODEL_C_API_KEY=...
export MODEL_D_API_KEY=...
```

如果使用 Docker Compose，默认会读取这些环境变量。不要把真实 key 写入 `config/config.example.yaml` 或提交本地 `config/config.yaml`。

## 3. Admin Surface

确认以下条件全部成立：

- `docker-compose.yml` 仍绑定 `127.0.0.1:8888:8888`，或外层反向代理/防火墙只允许内网访问。
- `server.admin_allowed_cidrs` 只包含 loopback、RFC1918、ULA 或明确受信的内网 CIDR。
- 没有在生产配置中加入 `0.0.0.0/0` 或 `::/0`。
- 启动日志显示 `router_auth=configured` 和 `admin_auth=configured`。
- `/admin/config` 返回的 `api_key`、`router_api_keys`、`admin_api_keys` 均为 `********`。

## 4. Smoke Test

```bash
curl http://127.0.0.1:8888/healthz
curl http://127.0.0.1:8888/readyz -H "Authorization: Bearer $ROUTER_API_KEY"
curl http://127.0.0.1:8888/admin/config -H "Authorization: Bearer $ADMIN_API_KEY"
```

从非允许网段访问 `/ui` 或 `/admin/config` 应返回 `403 admin_network_forbidden`。

## 5. Docker

```bash
docker compose up --build -d
docker compose ps
docker compose logs router
```

确认 healthcheck 正常，日志中没有启动配置回退或 DB 写入错误。
