# 配置与部署说明

本文档说明配置文件结构、上游 provider 鉴权方式、DB 模式和常见部署注意事项。

## 1. 配置文件加载

默认读取：

```bash
config/config.yaml
```

也可以通过环境变量指定：

```bash
export ROUTER_CONFIG=config/config.yaml
```

如果 `config/config.yaml` 不存在，应用会回退到：

```bash
config/config.example.yaml
```

配置文件支持 `${ENV_VAR}` 形式的环境变量插值，例如：

```yaml
api_key: ${MODEL_B_API_KEY}
```

## 2. 顶层结构

```yaml
server:
routing:
models:
telemetry:
estimation:
streaming:
```

各部分职责：
- `server`: Web 服务监听、请求大小限制、router API key、配置存储方式
- `routing`: evaluator、难度等级、路由映射、fallback 策略
- `models`: 上游 provider 定义、认证、限流、超时、健康参数
- `telemetry`: 日志和指标开关
- `estimation`: token 估算策略
- `streaming`: 流式透传控制

## 3. server 配置

常用字段：

```yaml
server:
  host: 0.0.0.0
  port: 8888
  request_timeout_seconds: 120
  max_request_body_mb: 8
  max_messages: 256
  max_tools: 128
  max_stop_sequences: 32
  max_message_chars: 200000
  max_tool_definition_chars: 400000
  config_source: db
  db_path: /app/data/router.db
  router_api_keys:
    - router-secret
```

`router_api_keys` 生效后，以下头都可用于访问路由器：
- `Authorization: Bearer <key>`
- `X-API-Key: <key>`
- `api-key: <key>`

## 4. routing 配置

最关键的几项是：

```yaml
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
```

含义：
- `enabled: true` 时，会先走 evaluator
- `evaluator_model` 是判定难度的模型
- `difficulty_to_model` 决定每个难度默认命中的模型

fallback 策略：

```yaml
fallback_policy:
  strategy: fallback
  ordered_candidates:
    easy: [model_b, model_c, model_d]
    medium: [model_c, model_d]
    hard: [model_d]
  max_fallback_hops: 2
  on_evaluator_error_use_default_difficulty: true
  queue_wait_ms: 250
  queue_poll_interval_ms: 25
```

支持三种行为：
- `fallback`: 当前模型失败或限流时尝试下一个候选
- `queue`: 没容量时等待短时间再重试获取容量
- `reject`: 没容量时直接返回 `429`

## 5. models 配置

每个模型都定义一个内部 key，例如：

```yaml
models:
  model_b:
    provider: openai_compatible
    provider_group: openai
    base_url: https://api.openai.com/v1
    api_key: ${MODEL_B_API_KEY}
    upstream_model_name: gpt-4.1-mini
    timeout_seconds: 60
    retry:
      max_attempts: 2
      backoff_initial_ms: 500
      backoff_max_ms: 2000
    limits:
      rpm: 300
      tpm: 300000
      concurrency: 32
    health:
      failure_threshold: 8
      cooldown_seconds: 20
```

### 5.1 `openai_compatible`

默认上游鉴权格式为：

```http
Authorization: Bearer <api_key>
```

可选字段：

```yaml
api_key_header: Authorization
api_key_prefix: "Bearer "
```

这两个字段可以改成任意兼容的 header 组合。例如某些 Azure 或企业网关要求：

```http
api-key: <token>
```

对应配置：

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

### 5.2 `openai-codex-oauth`

该 provider 从本地 token 文件读取 `access_token`：

```yaml
models:
  model_codex:
    provider: openai-codex-oauth
    provider_group: openai
    base_url: https://api.openai.com/v1
    oauth_token_path: /root/.codex/auth.json
    upstream_model_name: gpt-5.1-codex
    timeout_seconds: 120
    retry:
      max_attempts: 1
      backoff_initial_ms: 500
      backoff_max_ms: 2000
    limits:
      rpm: 60
      tpm: 120000
      concurrency: 8
```

特点：
- 不需要 `api_key`
- 默认 token 路径为空时会回退到 `~/.codex/auth.json`
- 始终使用 `Authorization: Bearer <access_token>`

## 6. DB 配置模式

如果要通过 `/ui` 或 `/admin/config` 动态修改配置，需要：

```yaml
server:
  config_source: db
  db_path: /app/data/router.db
```

行为说明：
- 启动时若 DB 为空，会把当前文件配置写入 SQLite
- 之后 UI 的保存操作会更新 DB，并重建服务实例
- 如果 DB 中存的配置损坏，应用会回退到文件配置并记录启动告警

## 7. Docker 注意事项

`docker-compose.yml` 默认已经考虑了两个挂载场景：
- `./data:/app/data`：持久化 SQLite 配置
- `${HOME}/.codex:/root/.codex:ro`：给 `openai-codex-oauth` provider 提供 token 文件

因此比较推荐的启动方式是：

```bash
docker compose up --build
```

## 8. 排障建议

### 路由器返回 401

检查：
- `server.router_api_keys` 是否配置
- 客户端是否发送了 `Authorization`、`X-API-Key` 或 `api-key`
- 代理层是否剥掉了这些头

### 上游返回 502 / upstream_auth_error

检查：
- `models.<name>.api_key` 是否正确
- 上游是否要求 `api-key` 而不是 `Authorization`
- `api_key_header` / `api_key_prefix` 是否配置正确
- OAuth token 文件是否存在、JSON 是否合法、是否包含 `tokens.access_token`

### UI 可以打开，但 `/metrics` 或管理接口调用失败

检查：
- UI 连接区是否填写了正确的 Router API Key
- 当前配置是否是 `config_source: db`
- 浏览器访问的 base URL 是否就是路由器实际地址
