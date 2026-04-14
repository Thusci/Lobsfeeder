# Lobsfeeder / openclaw-ai-router

OpenAI-compatible 路由网关，位于 OpenClaw 上游。

它支持：
- `POST /v1/chat/completions`（OpenAI 风格）
- 上游 provider：`openai_compatible`、`openai-codex-oauth`
- 评估模型先分类，再按难度路由到目标模型
- 每模型 RPM/TPM/并发限制
- 可选全局 RPM/并发限制
- 失败回退（fallback）与健康冷却（cooldown）
- 可配置容量策略：`fallback` / `queue` / `reject`
- 流式透传（`stream=true`）
- 请求级安全约束（消息数、tools 数、内容长度）
- `X-Request-ID` 透传到上游，便于链路追踪
- 结构化日志与 `/metrics`

## 快速开始

```bash
python -m pip install -r requirements.txt
cp config/config.example.yaml config/config.yaml
export MODEL_A_API_KEY=...
export MODEL_B_API_KEY=...
export MODEL_C_API_KEY=...
export MODEL_D_API_KEY=...
export ROUTER_CONFIG=config/config.yaml
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

## Docker

```bash
docker compose up --build
```

## 主要端点

- `POST /v1/chat/completions`
- `GET /healthz`
- `GET /readyz`
- `GET /metrics`
- `GET /debug/models`（启用 router api key 时需鉴权）
- `GET /ui` 控制台前端
- `GET /admin/config`（需鉴权）
- `POST /admin/config/validate`（需鉴权）
- `PUT /admin/config`（需鉴权，且需 `config_source=db`）

## 路由行为

- 默认：走 evaluator 分类后路由
- 直连绕过：`model` 直接填内部模型 key（如 `model_b`）
- 强制覆写：`model=force:model_b`
- 未知强制覆写：返回 `400`

## 容量策略

- `fallback`：当前模型无容量时尝试下一个候选模型
- `queue`：当前模型无容量时短暂等待，超时后返回 `429`
- `reject`：当前模型无容量时立即返回 `429`

## 测试

```bash
python -m pytest -q
```

## 控制台前端

启动后访问 `http://<host>:<port>/ui`，可进行健康检查、查看指标，并发送普通或流式 chat 请求。

## DB 配置模式

如果需要通过 UI 管理模型提供商，请在配置中设置：
- `server.config_source: db`
- `server.db_path: /app/data/router.db`

Docker Compose 已挂载 `./data:/app/data`，UI 中的 Config Manager 会读写该数据库并热切换服务配置。
默认示例配置已使用 `server.config_source: db`，因此通过 `docker compose up` 启动后，UI 中的编辑和保存会持久化到 `./data/router.db`。
为避免宿主机挂载目录的权限问题，容器默认以可写方式运行 SQLite 数据目录。
若使用 `openai-codex-oauth`，Compose 还会将宿主机 `${HOME}/.codex` 只读挂载到容器 `/root/.codex`，默认 token 路径为 `/root/.codex/auth.json`。

当前测试覆盖：
- 配置校验
- evaluator 输出解析容错
- override/候选生成
- RPM/TPM/并发限制
- 健康冷却
- 关键集成链路（评估、fallback、stream）
