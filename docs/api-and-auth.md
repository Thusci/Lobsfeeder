# API 与鉴权说明

本文档面向路由器调用方，说明外部 API、请求方式、响应头和 API key 鉴权行为。

## 1. 对外端点

### Chat

- `POST /v1/chat/completions`

用途：
- 兼容 OpenAI Chat Completions 请求
- 可由 evaluator 自动路由到内部模型
- 可直接指定内部模型绕过 routing

### 运维与管理

- `GET /healthz`
- `GET /readyz`
- `GET /metrics`
- `GET /debug/models`
- `GET /admin/config`（返回配置时会脱敏密钥字段）
- `POST /admin/config/validate`
- `PUT /admin/config`

## 2. 路由器 API key

`GET /healthz` 是公开的基础存活探针，不返回敏感信息。

除 `/healthz` 外，路由器端点都要求 API key。当 `server.router_api_keys` 为空时，这些端点会拒绝请求。

配置 key 后，支持以下三种头格式：

```http
Authorization: Bearer <key>
```

```http
X-API-Key: <key>
```

```http
api-key: <key>
```

这三种方式等价，便于同时兼容：
- OpenAI 风格 Bearer token 客户端
- 网关或浏览器工具偏好的 API key header
- 旧系统已经固定的 `api-key` 头

## 2.1 管理端 API key

`/admin/*` 管理接口支持独立的 `server.admin_api_keys`。

如果配置了 `admin_api_keys`，则管理接口优先要求这些 key。

如果 `admin_api_keys` 为空，则 `/admin/*` 会回退到 `server.router_api_keys`。

如果两组 key 都为空，`/admin/*` 会拒绝请求。

`/ui` 和 `/admin/*` 还会受 `server.admin_allowed_cidrs` 限制，默认只允许 loopback 与 RFC1918/ULA/link-local 内网地址。不要在生产中加入 `0.0.0.0/0`。

## 3. Chat 请求示例

### 自动路由

```bash
curl http://127.0.0.1:8888/v1/chat/completions \
  -H "Authorization: Bearer router-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "auto",
    "messages": [
      {"role": "system", "content": "You are concise."},
      {"role": "user", "content": "Summarize the current deployment state."}
    ]
  }'
```

### 直接指定内部模型

```bash
curl http://127.0.0.1:8888/v1/chat/completions \
  -H "X-API-Key: router-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "model_b",
    "messages": [
      {"role": "user", "content": "Answer directly with the cheaper model."}
    ]
  }'
```

### 强制绕过 evaluator

```bash
curl http://127.0.0.1:8888/v1/chat/completions \
  -H "api-key: router-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "force:model_d",
    "messages": [
      {"role": "user", "content": "Use the strongest model even if routing says otherwise."}
    ]
  }'
```

## 4. 请求字段

当前实现支持并透传以下常见字段：
- `model`
- `messages`
- `temperature`
- `top_p`
- `max_tokens`
- `stream`
- `stop`
- `presence_penalty`
- `frequency_penalty`
- `user`
- `tools`
- `tool_choice`
- `response_format`

请求还会受到以下安全限制影响：
- `server.max_request_body_mb`
- `server.max_messages`
- `server.max_tools`
- `server.max_stop_sequences`
- `server.max_message_chars`
- `server.max_tool_definition_chars`

超过限制时会返回 OpenAI 风格错误体。

## 5. 响应头

成功请求会附带这些路由相关响应头：
- `X-Request-ID`
- `X-Selected-Model`
- `X-Route-Mode`

说明：
- `X-Request-ID` 可用于串联客户端、路由器和上游日志
- `X-Selected-Model` 表示最终实际命中的内部模型 key
- `X-Route-Mode` 常见值为 `route` 或 `bypass`

## 6. 流式响应

当 `stream=true` 且服务端开启 `streaming.enabled` 与 `streaming.passthrough_streaming` 时，路由器会返回 `text/event-stream` 并透传上游流。

如果首个候选模型在真正开始出流前失败，路由器会尝试 fallback 到下一个候选模型；一旦流已经开始输出，则不会再切换模型。

## 7. 错误格式

路由器统一返回 OpenAI 风格错误体：

```json
{
  "error": {
    "message": "Missing API key. Use Authorization: Bearer <key>, X-API-Key, or api-key.",
    "type": "authentication_error",
    "code": "authentication_error"
  }
}
```

常见状态码：
- `400`: 请求参数无效、override 模型不存在、配置无效
- `401`: 缺少或错误的路由器 API key
- `429`: 限流命中或无容量
- `502`: 上游服务错误、鉴权失败、解析失败
- `503`: 没有可服务模型、健康熔断、服务未就绪
- `504`: 上游超时

## 8. UI 调用行为

`/ui` 控制台会：
- 内置中英双语切换
- 自动把输入的 Router API Key 同时兼容 raw key 和 Bearer token
- 为 `/admin/*` 提供单独的管理区解锁流程
- 用统一的请求封装访问 `/healthz`、`/readyz`、`/metrics`、`/admin/config`
- 对 `/metrics` 按文本响应处理，而不是错误地按 JSON 解析

如果 UI 能访问而脚本访问失败，优先检查：
- `server.router_api_keys` 是否已配置
- `server.admin_allowed_cidrs` 是否包含浏览器或反向代理访问路由器时的源 IP
- 是否使用了支持的三种鉴权头之一
- 反向代理是否转发了 `Authorization` / `X-API-Key`
