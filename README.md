# Lobsfeeder

OpenAI-compatible multi-model router for self-hosted LLM gateways.

面向自托管 LLM 网关的 OpenAI-compatible 多模型路由器。

## Disclaimer / 免责声明

Lobsfeeder is an independent community project. It is not affiliated with, endorsed by, or maintained by the official OpenClaw project or its maintainers. It can be used in front of OpenClaw or any other OpenAI-compatible client, but it is not an official OpenClaw component.

Lobsfeeder 是一个独立的社区项目，与 OpenClaw 官方项目及其维护者没有任何隶属、合作、背书或维护关系。它可以部署在 OpenClaw 或其他 OpenAI-compatible 客户端前方使用，但它不是 OpenClaw 的官方组件。

## Overview / 项目简介

Lobsfeeder exposes a standard `POST /v1/chat/completions` API and routes requests across multiple upstream models. It adds policy control, difficulty-based routing, rate limiting, fallback, health tracking, observability, and browser-based configuration tools on top of a familiar OpenAI-compatible interface.

Lobsfeeder 对外暴露标准 `POST /v1/chat/completions` 接口，并在多个上游模型之间完成请求路由。在熟悉的 OpenAI-compatible API 之上，它补充了策略控制、基于难度的路由、限流、回退、健康状态跟踪、可观测性以及浏览器配置工具。

Typical use cases:

典型使用场景：

- Unify multiple OpenAI-compatible backends behind one endpoint.
- 用一个统一入口整合多个 OpenAI-compatible 上游模型。
- Route requests by task difficulty, cost, latency, or operational policy.
- 按任务难度、成本、时延或运维策略选择模型。
- Add RPM, TPM, concurrency, and health protection without changing clients.
- 在不改调用方代码的前提下增加 RPM、TPM、并发和健康保护。
- Keep OpenAI-style requests while gaining a controllable gateway layer.
- 保持 OpenAI 风格调用方式，同时获得更可控的网关层。
- Manage model settings from a browser UI with DB-backed persistence.
- 通过浏览器 UI 管理模型配置，并支持 DB 持久化。

## Table Of Contents / 目录

- [Why Lobsfeeder / 为什么使用 Lobsfeeder](#why-lobsfeeder--为什么使用-lobsfeeder)
- [Core Features / 核心特性](#core-features--核心特性)
- [How It Works / 工作原理](#how-it-works--工作原理)
- [Architecture / 系统架构](#architecture--系统架构)
- [Quick Start / 快速开始](#quick-start--快速开始)
- [Configuration / 配置说明](#configuration--配置说明)
- [Common Operations / 常用操作](#common-operations--常用操作)
- [Endpoints / 主要端点](#endpoints--主要端点)
- [Authentication / 鉴权说明](#authentication--鉴权说明)
- [Observability / 观测与运维](#observability--观测与运维)
- [Development / 开发指南](#development--开发指南)
- [Project Structure / 项目结构](#project-structure--项目结构)
- [More Docs / 补充文档](#more-docs--补充文档)
- [License](#license)

## Why Lobsfeeder / 为什么使用 Lobsfeeder

When several models sit behind one product, client code quickly becomes messy: one service decides which model to use, another tracks rate limits, a third handles fallback, and nobody knows where to look when a request fails. Lobsfeeder centralizes those decisions into one router layer.

当一个产品背后同时接入多个模型时，调用层很容易变得混乱：一处代码负责选模型，一处负责限流，一处负责回退，出了问题还很难知道该看哪里。Lobsfeeder 的价值就在于把这些决策统一收敛到一个路由层。

Benefits:

优势：

- Decouple model selection from application code.
- 把模型选择逻辑从业务代码中解耦出来。
- Keep a single OpenAI-compatible entry point for existing clients and tools.
- 为现有客户端和工具保留统一的 OpenAI-compatible 入口。
- Enforce routing, fallback, and protection policies consistently.
- 统一执行路由、回退和保护策略。
- Improve operational visibility with health, metrics, and debug endpoints.
- 通过健康检查、指标和调试端点提升可运维性。
- Allow dynamic config updates through a DB-backed admin flow.
- 通过基于 DB 的管理流程支持动态配置更新。

## Core Features / 核心特性

- Standard `POST /v1/chat/completions` API.
- 标准 `POST /v1/chat/completions` 接口。
- Upstream providers: `openai_compatible` and `openai-codex-oauth`.
- 支持 `openai_compatible` 与 `openai-codex-oauth` 两类上游 provider。
- Evaluator-first routing based on difficulty classification.
- 支持先经 evaluator 判断难度，再按难度路由。
- Explicit bypass with internal model keys or `force:<model_key>`.
- 支持通过内部模型 key 或 `force:<model_key>` 显式绕过路由。
- Per-model RPM, TPM, and concurrency limits.
- 支持按模型维度配置 RPM、TPM 和并发限制。
- Optional global capacity controls.
- 支持可选的全局容量限制。
- Fallback, queue, and reject capacity strategies.
- 提供 fallback、queue、reject 三种容量策略。
- Stream passthrough for `stream=true`.
- 支持 `stream=true` 的流式透传。
- Health cooldown and request-level input limits.
- 支持健康冷却和请求级输入限制。
- Built-in browser UI with English and Chinese i18n, admin unlock flow, and DB-backed config editing.
- 提供内置中英双语浏览器 UI，支持管理区解锁与基于 DB 的配置编辑。

## How It Works / 工作原理

Request flow:

请求流程：

1. Client sends an OpenAI-style chat completion request to `/v1/chat/completions`.
1. 客户端向 `/v1/chat/completions` 发送 OpenAI 风格请求。
2. Lobsfeeder validates request size, message count, tools count, and router auth.
2. Lobsfeeder 校验请求体大小、消息数量、tools 数量和路由器鉴权。
3. If routing is enabled and not bypassed, an evaluator model classifies difficulty.
3. 若启用路由且未被绕过，则先由 evaluator 模型判断难度。
4. The router builds candidate models from difficulty mapping and fallback policy.
4. 路由器根据难度映射和 fallback 策略生成候选模型。
5. Rate limit and health checks decide whether a candidate can serve the request.
5. 结合限流状态和健康状态判断候选模型是否可服务。
6. The request is forwarded upstream with an `X-Request-ID`.
6. 请求会携带 `X-Request-ID` 转发给上游。
7. On failure, timeout, or no capacity, the router can fallback according to policy.
7. 当失败、超时或无容量时，路由器可按策略回退到其他模型。
8. The final response is returned in an OpenAI-compatible shape.
8. 最终以 OpenAI-compatible 的响应格式返回给调用方。

## Architecture / 系统架构

```text
Client / OpenClaw / Script / SDK
               |
               v
        Lobsfeeder Router
          - Request validation
          - Router API auth
          - Difficulty evaluation
          - Model selection
          - Rate limiting
          - Health tracking
          - Metrics and debugging
               |
               +--> Model A (evaluator)
               +--> Model B (cheap / fast)
               +--> Model C (balanced)
               +--> Model D (strongest)
```

## Quick Start / 快速开始

### Local Run / 本地运行

Requirements:

环境要求：

- Python 3.11+
- Python 3.11+
- Reachable OpenAI-compatible upstream services
- 可访问的 OpenAI-compatible 上游服务

Install and start:

安装并启动：

```bash
python -m pip install -r requirements.txt
cp config/config.example.yaml config/config.yaml

export MODEL_A_API_KEY=...
export MODEL_B_API_KEY=...
export MODEL_C_API_KEY=...
export MODEL_D_API_KEY=...
export ROUTER_CONFIG=config/config.yaml

PYTHONPATH=. uvicorn app.main:app --host 0.0.0.0 --port 8888
```

Useful local URLs:

本地常用地址：

- `http://127.0.0.1:8888/ui`
- `http://127.0.0.1:8888/healthz`
- `http://127.0.0.1:8888/readyz`
- `http://127.0.0.1:8888/metrics`

### Docker Run / Docker 运行

```bash
docker compose up --build
```

Default `docker-compose.yml` behavior:

默认 `docker-compose.yml` 行为：

- Mounts `config/config.example.yaml` as `/app/config/config.yaml`
- 将 `config/config.example.yaml` 挂载为容器内 `/app/config/config.yaml`
- Mounts `./data` for SQLite-backed config persistence
- 将 `./data` 挂载为 SQLite 配置持久化目录
- Mounts `${HOME}/.codex` read-only for OAuth token provider use
- 将 `${HOME}/.codex` 只读挂载给 OAuth token provider 使用

For UI-based persistent config editing, keep:

若希望通过 UI 保存并持久化配置，建议保持：

- `server.config_source: db`
- `server.db_path: /app/data/router.db`

## Configuration / 配置说明

The default config path is:

默认配置路径为：

```bash
config/config.yaml
```

You can also override it with:

也可以通过环境变量覆盖：

```bash
export ROUTER_CONFIG=config/config.yaml
```

Top-level config sections:

顶层配置分区：

- `server`: network binding, request limits, router API keys, config source
- `server`：监听地址、请求限制、路由器 API key、配置来源
- `routing`: evaluator, difficulty levels, model mapping, fallback policy
- `routing`：evaluator、难度等级、模型映射、fallback 策略
- `models`: upstream provider settings, auth, timeout, retry, limits, health
- `models`：上游 provider、鉴权、超时、重试、限流、健康参数
- `telemetry`: logs and metrics behavior
- `telemetry`：日志和指标行为
- `estimation`: token estimation behavior
- `estimation`：token 估算策略
- `streaming`: stream passthrough options
- `streaming`：流式透传配置

Key example:

关键配置示例：

```yaml
server:
  host: 0.0.0.0
  port: 8888
  config_source: db
  db_path: /app/data/router.db
  router_api_keys:
    - router-secret
  admin_api_keys:
    - admin-secret

routing:
  enabled: true
  evaluator_model: model_a
  default_difficulty: medium
  difficulty_levels: [easy, medium, hard, expert]
  difficulty_to_model:
    easy: model_b
    medium: model_c
    hard: model_d
    expert: model_d

models:
  model_a:
    provider: openai_compatible
    provider_group: openai
    base_url: http://host.docker.internal:9001/v1
    api_key: ${MODEL_A_API_KEY}
    upstream_model_name: judge-model
    limits:
      rpm: 120
      tpm: 120000
      concurrency: 8
```

See the full sample in [config/config.example.yaml](config/config.example.yaml).

完整示例请见 [config/config.example.yaml](config/config.example.yaml)。

## Common Operations / 常用操作

### 1. Check Service Health / 检查服务状态

Without router auth:

未启用路由器鉴权时：

```bash
curl http://127.0.0.1:8888/healthz
curl http://127.0.0.1:8888/readyz
```

With router auth enabled:

启用路由器鉴权后：

```bash
curl http://127.0.0.1:8888/healthz \
  -H "Authorization: Bearer router-secret"
```

### 2. Send an Auto-Routed Request / 发送自动路由请求

```bash
curl http://127.0.0.1:8888/v1/chat/completions \
  -H "Authorization: Bearer router-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "auto",
    "messages": [
      {"role": "system", "content": "You are concise."},
      {"role": "user", "content": "Give me a short deployment summary."}
    ]
  }'
```

This request goes through the evaluator first.

这类请求默认会先经过 evaluator。

### 3. Pin a Specific Internal Model / 直接指定内部模型

```bash
curl http://127.0.0.1:8888/v1/chat/completions \
  -H "X-API-Key: router-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "model_b",
    "messages": [
      {"role": "user", "content": "Answer with the cheaper model."}
    ]
  }'
```

### 4. Force Bypass Routing / 强制绕过路由

```bash
curl http://127.0.0.1:8888/v1/chat/completions \
  -H "api-key: router-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "force:model_d",
    "messages": [
      {"role": "user", "content": "Use the strongest model directly."}
    ]
  }'
```

### 5. Use the Browser UI / 使用浏览器 UI

Open:

打开：

```text
http://127.0.0.1:8888/ui
```

You can:

你可以：

- Switch between built-in English and Chinese UI copy
- 在内置英文和中文界面之间切换
- Probe `/healthz`, `/readyz`, `/metrics`, and `/debug/models`
- 调用 `/healthz`、`/readyz`、`/metrics`、`/debug/models`
- Send standard or streaming chat requests
- 发送普通或流式 chat 请求
- Unlock admin panels, then load, validate, save, and apply DB-backed config
- 先解锁管理面板，再加载、校验、保存并应用基于 DB 的配置
- Add providers, edit model settings, and switch OAuth mode
- 新增 provider、编辑模型参数、切换 OAuth 模式

### 6. Inspect Metrics And Debug Data / 查看指标与调试信息

```bash
curl http://127.0.0.1:8888/metrics \
  -H "Authorization: Bearer router-secret"

curl http://127.0.0.1:8888/debug/models \
  -H "Authorization: Bearer router-secret"
```

### 7. Change Upstream API-Key Format / 修改上游 API-Key 格式

Default upstream auth for `openai_compatible`:

`openai_compatible` 默认上游鉴权格式：

```http
Authorization: Bearer <api_key>
```

If your upstream expects:

如果你的上游要求：

```http
api-key: <token>
```

configure:

则配置为：

```yaml
models:
  azure_like_model:
    provider: openai_compatible
    provider_group: azure
    base_url: https://example.openai.azure.com/openai/deployments/chat/v1
    api_key: ${AZURE_API_KEY}
    api_key_header: api-key
    api_key_prefix: ""
    upstream_model_name: gpt-4.1-mini
    timeout_seconds: 60
    retry:
      max_attempts: 2
      backoff_initial_ms: 300
      backoff_max_ms: 1500
    limits:
      rpm: 120
      tpm: 120000
      concurrency: 8
```

### 8. Use OAuth Provider / 使用 OAuth Provider

For `openai-codex-oauth`:

对于 `openai-codex-oauth`：

- No `api_key` is required
- 不需要填写 `api_key`
- `oauth_token_path` is used to load the access token
- 会通过 `oauth_token_path` 读取 access token
- Empty path falls back to `~/.codex/auth.json`
- 若路径为空，会回退到 `~/.codex/auth.json`
- Upstream auth is always `Authorization: Bearer <access_token>`
- 上游请求始终使用 `Authorization: Bearer <access_token>`

## Endpoints / 主要端点

| Endpoint | Method | English | 中文 |
| --- | --- | --- | --- |
| `/v1/chat/completions` | `POST` | OpenAI-compatible chat completions | OpenAI-compatible 聊天接口 |
| `/healthz` | `GET` | Basic health probe | 基础健康检查 |
| `/readyz` | `GET` | Readiness probe | 就绪状态检查 |
| `/metrics` | `GET` | Prometheus metrics | Prometheus 指标 |
| `/debug/models` | `GET` | Model health and limit snapshot | 模型健康与限流快照 |
| `/admin/config` | `GET` | Read current config | 读取当前配置 |
| `/admin/config/validate` | `POST` | Validate config payload | 校验配置是否合法 |
| `/admin/config` | `PUT` | Save and hot-apply config | 保存并热应用配置 |
| `/ui` | `GET` | Browser control console | 浏览器控制台 |

## Authentication / 鉴权说明

### Router Auth / 路由器鉴权

If `server.router_api_keys` is empty, router endpoints are public.

如果 `server.router_api_keys` 为空，则路由器端点默认不鉴权。

If it is configured, the router accepts any of the following:

如果配置了 key，则支持以下任意一种写法：

- `Authorization: Bearer <key>`
- `X-API-Key: <key>`
- `api-key: <key>`

### Admin Auth / 管理端鉴权

`/admin/*` routes support a dedicated key set via `server.admin_api_keys`.

`/admin/*` 路由支持通过 `server.admin_api_keys` 配置独立管理 key。

If `admin_api_keys` is empty, admin routes fall back to `router_api_keys`.

如果 `admin_api_keys` 为空，管理端路由会回退使用 `router_api_keys`。

### Upstream Auth / 上游鉴权

Supported upstream auth modes:

支持的上游鉴权方式：

- `openai_compatible`
- `openai-codex-oauth`

`openai_compatible` defaults to Bearer auth, but can customize header name and prefix.

`openai_compatible` 默认使用 Bearer 认证，但支持自定义 header 名称和前缀。

`openai-codex-oauth` loads `tokens.access_token` from a local JSON token file.

`openai-codex-oauth` 会从本地 JSON token 文件中读取 `tokens.access_token`。

## Observability / 观测与运维

Built-in operational capabilities:

内建运维能力：

- `/healthz` and `/readyz` probes
- `/healthz` 与 `/readyz` 探针
- `/metrics` for Prometheus scraping
- `/metrics` 可供 Prometheus 抓取
- `X-Request-ID` propagation for request tracing
- `X-Request-ID` 透传用于链路追踪
- Health cooldown when repeated failures occur
- 连续失败后的健康冷却机制
- `/debug/models` for internal snapshots
- `/debug/models` 用于查看内部状态快照

Recommended operational practices:

建议的运维实践：

- Use `/readyz` for readiness checks.
- 使用 `/readyz` 作为 readiness 检查。
- Scrape `/metrics` with Prometheus.
- 使用 Prometheus 抓取 `/metrics`。
- Pass `X-Request-ID` from the caller whenever possible.
- 尽量从调用侧透传 `X-Request-ID`。
- Set strong random router API keys in production.
- 生产环境请使用强随机值作为路由器 API key。

## Development / 开发指南

Install dependencies:

安装依赖：

```bash
python -m pip install -r requirements.txt
```

Run tests:

运行测试：

```bash
PYTHONPATH=. pytest -q
```

Run the app locally with reload:

本地热重载运行：

```bash
PYTHONPATH=. uvicorn app.main:app --reload --host 0.0.0.0 --port 8888
```

## Project Structure / 项目结构

```text
app/
  api/          FastAPI routes and request dependencies
  clients/      Upstream OpenAI-compatible clients and auth
  core/         Settings, lifecycle, logging, errors
  evaluator/    Difficulty prompts, parsing, and evaluator service
  ratelimit/    RPM / TPM / concurrency control
  router/       Selection, fallback, dispatcher, health policies
  telemetry/    Metrics and tracing helpers
  ui/           Browser control console
config/         Config examples and schema
tests/          Unit and integration tests
```

## More Docs / 补充文档

- [API And Auth Guide / API 与鉴权说明](docs/api-and-auth.md)
- [Configuration Guide / 配置与部署说明](docs/configuration.md)
- [Example Config / 示例配置](config/config.example.yaml)

## License

This repository is licensed under GPL v3. See [LICENSE](LICENSE).

本仓库采用 GPL v3 开源协议，详见 [LICENSE](LICENSE)。
