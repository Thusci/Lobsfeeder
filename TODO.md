下面是一份**完整 `TODO.md`**。它面向一个 **OpenAI-compatible Router**：作为 OpenClaw 的上游 API 网关，接收 `/v1/chat/completions` 请求，先调用“评估模型”判定任务难度，再把请求路由到对应模型，同时支持每个模型独立的 RPM、TPM、并发限制。OpenClaw 本身支持 Docker 部署与网关式工作流；Chat Completions 端点以 `messages` 为核心输入，这与本项目的代理目标一致。([GitHub][1])
# TODO.md — openclaw-ai-router

## 1. Project goal

Build a production-grade OpenAI-compatible routing gateway for OpenClaw.

The gateway must:
- expose an OpenAI-compatible `POST /v1/chat/completions` endpoint
- accept standard chat-completions style requests
- optionally classify task difficulty using a dedicated evaluator model first
- route the original request to a target model based on configurable difficulty tiers
- support configurable per-model rate limiting:
  - requests per minute (RPM)
  - tokens per minute (TPM)
  - concurrency
- support fallback and degradation when a model is unavailable, overloaded, or rate-limited
- preserve OpenAI-style response shape as much as practical
- be robust enough for long-running self-hosted use behind OpenClaw

---

## 2. Non-goals

Do not implement:
- training, fine-tuning, or any model serving backend
- non-OpenAI API provider adapters in the first version unless they are already OpenAI-compatible
- a frontend UI in v1
- full billing/accounting in v1
- persistent distributed rate limiting in v1 unless explicitly configured

---

## 3. High-level architecture

Request flow:

1. OpenClaw sends a request to this router using OpenAI-compatible chat completions.
2. Router validates input and assigns a request ID.
3. Router determines whether to bypass evaluation:
   - if request explicitly pins a route target or routing is disabled, skip evaluator
   - otherwise continue
4. Router calls evaluator model (Model A) with a strict classification prompt.
5. Router parses evaluator output into a normalized difficulty tier.
6. Router maps difficulty tier to a target model according to config.
7. Router checks that target model is currently available under its rate limits and health state.
8. If available, router forwards the original user request to that target model.
9. If not available, router applies fallback policy:
   - next configured model
   - queue
   - reject
10. Router returns a standard OpenAI-style response.
11. Router logs structured telemetry for debugging and analytics.

---

## 4. Core requirements

### 4.1 API compatibility

Must implement:
- `POST /v1/chat/completions`

Should support these request fields in v1:
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
- `response_format` if practical

Must return:
- `id`
- `object`
- `created`
- `model`
- `choices`
- `usage` when available

If upstream provider omits usage, estimate and populate best-effort usage metadata.

### 4.2 Routing behavior

Must support:
- one evaluator model
- N difficulty tiers
- N routable downstream models
- config-driven tier-to-model mapping
- explicit request override to bypass evaluator

### 4.3 Rate limiting

Must support per-model:
- RPM
- TPM
- concurrency

Must support global:
- optional total concurrency cap
- optional total RPM cap

### 4.4 Reliability

Must support:
- timeout
- retry with bounded backoff
- evaluator failure fallback
- target model failure fallback
- malformed evaluator output fallback
- structured error responses
- health tracking / temporary cooldown

---

## 5. Suggested project structure

Use Python + FastAPI for v1.

Suggested layout:

.
├── app
│   ├── api
│   │   ├── routes_chat.py
│   │   ├── routes_health.py
│   │   └── schemas.py
│   ├── core
│   │   ├── settings.py
│   │   ├── logging.py
│   │   ├── errors.py
│   │   ├── ids.py
│   │   └── lifecycle.py
│   ├── clients
│   │   ├── openai_compat_client.py
│   │   └── registry.py
│   ├── evaluator
│   │   ├── prompt.py
│   │   ├── service.py
│   │   └── parser.py
│   ├── router
│   │   ├── policy.py
│   │   ├── dispatcher.py
│   │   ├── fallback.py
│   │   └── selection.py
│   ├── ratelimit
│   │   ├── rpm.py
│   │   ├── tpm.py
│   │   ├── concurrency.py
│   │   ├── manager.py
│   │   └── estimation.py
│   ├── telemetry
│   │   ├── metrics.py
│   │   └── tracing.py
│   └── main.py
├── config
│   ├── config.example.yaml
│   └── config.schema.json
├── tests
│   ├── unit
│   ├── integration
│   └── fixtures
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── TODO.md

---

## 6. Configuration design

Implement YAML config loading and validation.

### 6.1 Example config

```yaml
server:
  host: 0.0.0.0
  port: 8080
  request_timeout_seconds: 120
  max_request_body_mb: 8

routing:
  enabled: true
  evaluator_model: model_a
  default_difficulty: medium
  allow_request_override: true
  override_field_mode: alias
  difficulty_levels:
    - easy
    - medium
    - hard
    - expert
  difficulty_to_model:
    easy: model_b
    medium: model_c
    hard: model_d
    expert: model_d
  fallback_policy:
    strategy: fallback
    ordered_candidates:
      easy: [model_b, model_c, model_d]
      medium: [model_c, model_d]
      hard: [model_d]
      expert: [model_d]
    max_fallback_hops: 2
    on_evaluator_error_use_default_difficulty: true

models:
  model_a:
    provider: openai_compatible
    base_url: http://host.docker.internal:9001/v1
    api_key: ${MODEL_A_API_KEY}
    upstream_model_name: judge-model
    timeout_seconds: 20
    retry:
      max_attempts: 2
      backoff_initial_ms: 300
      backoff_max_ms: 1500
    limits:
      rpm: 120
      tpm: 120000
      concurrency: 8
    health:
      failure_threshold: 5
      cooldown_seconds: 30

  model_b:
    provider: openai_compatible
    base_url: http://host.docker.internal:9002/v1
    api_key: ${MODEL_B_API_KEY}
    upstream_model_name: cheap-fast-model
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

  model_c:
    provider: openai_compatible
    base_url: http://host.docker.internal:9003/v1
    api_key: ${MODEL_C_API_KEY}
    upstream_model_name: balanced-model
    timeout_seconds: 90
    retry:
      max_attempts: 2
      backoff_initial_ms: 700
      backoff_max_ms: 3000
    limits:
      rpm: 180
      tpm: 180000
      concurrency: 16
    health:
      failure_threshold: 6
      cooldown_seconds: 25

  model_d:
    provider: openai_compatible
    base_url: http://host.docker.internal:9004/v1
    api_key: ${MODEL_D_API_KEY}
    upstream_model_name: strongest-model
    timeout_seconds: 120
    retry:
      max_attempts: 1
      backoff_initial_ms: 1000
      backoff_max_ms: 3000
    limits:
      rpm: 60
      tpm: 240000
      concurrency: 8
    health:
      failure_threshold: 4
      cooldown_seconds: 45

telemetry:
  structured_logs: true
  log_level: INFO
  expose_metrics: true

estimation:
  token_strategy: best_effort
  chars_per_token_fallback: 4

streaming:
  enabled: true
  evaluator_streaming: false
  passthrough_streaming: true
````

### 6.2 Config requirements

* support environment variable interpolation
* validate required fields on startup
* reject invalid tier mappings
* reject references to undefined models
* reject duplicate difficulty names
* validate numeric ranges for rate limits and timeouts
* optionally support live reload later, but not required in v1

---

## 7. Request contract and routing override

### 7.1 Primary request contract

Default behavior:

* client sends OpenAI-compatible chat request
* `model` field may be a logical alias handled by this router

### 7.2 Override behavior

Support one or more of:

* `model` equals a logical route alias like `force:model_d`
* extra header like `X-Route-Model: model_d`
* metadata field in a safe extension object if present

Implement only one override mechanism in v1 and document it clearly.

Recommended v1:

* if request `model` exactly matches a configured internal model key, bypass evaluator and use that model directly
* otherwise treat request as routable and evaluate difficulty

### 7.3 Safe defaults

* if override points to an unknown model, return 400
* if override points to a known but unhealthy/rate-limited model, still allow fallback unless strict mode is enabled

---

## 8. Evaluator design

### 8.1 Evaluator responsibilities

Evaluator model must:

* inspect the original user task
* classify it into one configured difficulty tier
* optionally provide a short reason
* never answer the user’s actual task

### 8.2 Evaluator prompt design

Create a strict system prompt template that:

* explains allowed difficulty tiers dynamically from config
* forbids normal answering
* requires valid JSON only
* minimizes verbosity

Example template:

You are a task difficulty classifier for an LLM routing gateway.
Your job is to classify the user's request into exactly one difficulty tier.

Allowed tiers:
{{ difficulty_levels | join(", ") }}

Return JSON only:
{
"difficulty": "<one allowed tier>",
"reason": "<brief reason, max 20 words>"
}

Rules:

* Do not answer the user’s task.
* Do not include markdown.
* Do not include code fences.
* If uncertain, choose the nearest reasonable tier.

### 8.3 Evaluator input shaping

Implement a function to convert original request into evaluator input:

* include system messages only if configured
* include recent user/assistant turns
* truncate safely by character or token budget
* include tool definitions only if later testing shows they improve classification
* avoid forwarding giant contexts unnecessarily

### 8.4 Evaluator output parser

Must parse robustly:

* plain JSON
* JSON surrounded by whitespace
* JSON wrapped in stray text
* malformed outputs with recoverable tier mentions

Parsing policy:

1. attempt strict JSON parse
2. attempt JSON extraction from first balanced object
3. attempt regex recovery for tier value
4. else fallback to configured default difficulty

Normalize:

* case-insensitive tier names
* trim whitespace
* reject unrecognized tiers

### 8.5 Evaluator timeout and failure handling

If evaluator:

* times out
* returns invalid content
* returns upstream 429
* returns upstream 5xx
* is unhealthy

Then:

* use configured default difficulty
* add a structured log event with reason
* continue routing rather than failing the user request unless strict mode is enabled

---

## 9. Downstream OpenAI-compatible client

### 9.1 Implement reusable async client

Create `OpenAICompatClient` with:

* base URL
* API key
* default timeout
* connection pooling
* retry policy
* streaming support

### 9.2 Must support

* `POST /chat/completions`
* custom headers
* streaming and non-streaming modes
* usage extraction when present
* error mapping

### 9.3 Error mapping

Map upstream errors into internal categories:

* auth_error
* bad_request
* rate_limited
* timeout
* transient_upstream
* permanent_upstream
* parse_error
* unknown

### 9.4 Response normalization

Return a normalized internal structure so router logic does not depend on raw provider quirks.

---

## 10. Rate limiting design

Implement per-model local rate limiting.

### 10.1 RPM limiter

Use sliding-window or token-bucket.
Requirements:

* count accepted requests per 60-second rolling window
* reject or defer requests exceeding model RPM
* remain async-safe under concurrency

### 10.2 TPM limiter

Implement token accounting.
Requirements:

* estimate input tokens before dispatch
* reserve projected tokens before request if configured
* reconcile after response using actual usage if available
* support separate tracking for input and output later, but total TPM is enough in v1

### 10.3 Concurrency limiter

Use async semaphore per model.
Requirements:

* acquire before dispatch
* release on success, failure, timeout, or cancellation
* never leak permits

### 10.4 Estimation strategy

Implement a best-effort token estimator.
Priority:

1. actual `usage.total_tokens` from upstream response
2. provider-specific usage fields if compatible
3. fallback estimator using text length and configurable chars-per-token heuristic

### 10.5 Rate limit manager

Create one manager per process with:

* lookup by model key
* `can_accept(model, estimated_tokens)`
* `acquire(model, estimated_tokens)`
* `finalize(model, estimated_tokens, actual_tokens, outcome)`

### 10.6 Rate limit strategies

Support config option:

* `fallback`: try another candidate model
* `queue`: wait briefly for capacity
* `reject`: return 429 immediately

Implement `fallback` first.
Implement `queue` only if simple and bounded.
Do not allow unbounded queues.

---

## 11. Routing and selection logic

### 11.1 Core routing steps

For each incoming request:

1. validate request
2. compute request ID
3. determine bypass or evaluate
4. classify difficulty if needed
5. build ordered candidate list
6. for each candidate:

   * check health
   * check rate limit capacity
   * acquire capacity
   * call provider
   * on success finalize and return
   * on failure finalize and continue if retryable
7. if no candidate succeeds, return structured error

### 11.2 Candidate list generation

If difficulty is `medium`, example candidates may be:

* primary from mapping: `model_c`
* fallbacks from config: `model_d`

Do not include duplicates.
Do not include evaluator model unless explicitly configured as a serving candidate.

### 11.3 Health-aware routing

Track model health using rolling failures:

* increment on timeout, connection error, repeated 5xx
* optionally do not increment on 4xx from bad user input
* when threshold exceeded, mark model unhealthy until cooldown elapses

### 11.4 Retry policy

Retries happen at two layers:

* upstream call retry within same model for short transient failures
* router-level fallback across models

Avoid retry storms:

* keep retry counts low
* do not retry non-idempotent streaming once bytes are emitted
* do not retry obvious 4xx request errors

---

## 12. Streaming support

### 12.1 Scope

Support `stream: true` for downstream response passthrough.
Evaluator itself does not need streaming.

### 12.2 Behavior

For streamed requests:

* still run evaluator synchronously first
* then open streaming connection to selected target model
* relay SSE chunks to client with minimal transformation
* preserve OpenAI-like stream event format where possible

### 12.3 Failure behavior

If streaming target fails before first chunk:

* fallback to another model is allowed
  If streaming target fails after first chunk:
* do not fallback automatically in v1
* terminate stream and log error

---

## 13. Error handling contract

### 13.1 Client-visible errors

Return JSON errors in OpenAI-like format where practical:

* 400 invalid request
* 401 invalid auth to router if enabled
* 404 unknown route/model alias
* 408 or 504 timeout
* 429 rate limited / no capacity
* 502 bad upstream
* 503 all backends unavailable
* 500 unexpected internal error

### 13.2 Internal error classes

Implement explicit exceptions:

* ValidationError
* EvaluatorError
* RoutingError
* NoCapacityError
* UpstreamTimeoutError
* UpstreamRateLimitError
* UpstreamServerError
* UpstreamClientError
* HealthCircuitOpenError

### 13.3 Safe logging

Never log raw API keys.
Avoid logging full prompts unless debug mode is explicitly enabled.
Redact sensitive headers and secrets.

---

## 14. Logging and telemetry

### 14.1 Structured logging

Every request log should include:

* request_id
* timestamp
* route_mode: evaluated or bypass
* evaluator_model
* difficulty
* selected_model
* fallback_hops
* estimated_tokens
* actual_tokens if known
* response_status
* latency_ms
* error_category if any

### 14.2 Metrics

Expose optional Prometheus-style metrics:

* total_requests
* successful_requests
* failed_requests
* evaluator_failures
* per_model_requests
* per_model_rate_limit_hits
* per_model_fallback_from
* per_model_timeouts
* per_model_latency_histogram
* current_per_model_concurrency
* unhealthy_models_count

### 14.3 Tracing

Optional later:

* OpenTelemetry traces
* span for evaluator
* span for each candidate attempt

---

## 15. Security and access control

### 15.1 Router auth

Support optional incoming router API key.
If enabled:

* require `Authorization: Bearer ...`
* validate against configured keys or single shared key

### 15.2 Request size limits

Reject:

* oversized request bodies
* excessively large messages arrays
* giant tool definitions if configured

### 15.3 SSRF / URL safety

Do not accept downstream base URLs from request payload.
All providers must come from server config only.

---

## 16. Health and admin endpoints

Implement:

* `GET /healthz` basic process health
* `GET /readyz` readiness based on config + internal state
* `GET /metrics` optional metrics
* `GET /debug/models` optional protected debug endpoint showing model states:

  * healthy/unhealthy
  * current concurrency
  * last error
  * recent rate limit hits

Do not expose secrets.

---

## 17. Testing plan

### 17.1 Unit tests

Write tests for:

* config validation
* evaluator parser
* difficulty normalization
* request override logic
* RPM limiter
* TPM limiter
* concurrency limiter
* fallback candidate generation
* health cooldown logic
* token estimation

### 17.2 Integration tests

Create mock OpenAI-compatible upstream servers and test:

* successful evaluated route to model_b
* successful evaluated route to model_c
* evaluator timeout falling back to default difficulty
* primary target 429 causing fallback to next model
* primary target 5xx causing fallback to next model
* all candidates failing returns 503
* bypass route works
* unknown override returns 400
* streaming passthrough works
* streaming first-target failure before first chunk falls back
* streaming failure after first chunk terminates correctly

### 17.3 Load / concurrency tests

Test:

* concurrency semaphore correctness
* no permit leaks under cancellations
* rate limiter correctness under high concurrent load
* latency under evaluator + target chain
* fallback storms under capacity pressure

### 17.4 Regression fixtures

Store representative request payloads:

* simple chat
* tool-calling request
* long-context request
* streaming request
* malformed request

---

## 18. Docker and deployment

### 18.1 Dockerfile

Requirements:

* slim base image
* install dependencies
* non-root runtime user if practical
* expose configured port
* healthcheck command
* copy config example but mount real config externally

### 18.2 docker-compose.yml

Include service:

* router
* mounted config
* env file support
* optional host access if local upstream models are on host

### 18.3 Deployment assumptions

This router is intended to sit in front of OpenClaw.
OpenClaw can then be pointed at this router’s OpenAI-compatible base URL instead of a single provider directly. OpenClaw’s documented Docker workflow and onboarding flow make this gateway pattern practical in a self-hosted deployment. ([GitHub][1])

---

## 19. Implementation milestones

### Milestone 1: skeleton

* create FastAPI app
* add config loader
* add `/healthz`
* add `/v1/chat/completions` returning stub response

### Milestone 2: single-model proxy

* implement one OpenAI-compatible upstream client
* forward non-streaming requests to one configured model
* return normalized response

### Milestone 3: evaluator

* implement evaluator prompt, call, parser
* route based on difficulty
* add config for tiers and mapping

### Milestone 4: rate limits

* implement RPM, TPM, concurrency per model
* enforce before dispatch
* add metrics

### Milestone 5: fallback and health

* implement fallback chains
* add cooldowns and unhealthy states
* improve error handling

### Milestone 6: streaming

* add stream passthrough
* handle pre-first-chunk fallback

### Milestone 7: hardening

* add tests
* add structured logging
* add Docker packaging
* add docs and example config

---

## 20. Acceptance criteria

Project is complete when all of the following are true:

1. OpenClaw can send a standard chat-completions request to this service and receive a valid response in OpenAI-compatible shape. The OpenAI chat-completions contract centers on `messages`, which this router must preserve when proxying. ([OpenAI Developers][2])
2. Evaluator model can classify at least 4 tiers from config and router uses that classification.
3. Request can bypass evaluator by explicitly selecting an internal model key.
4. Per-model RPM, TPM, and concurrency limits are enforced.
5. When the primary model is rate-limited or unhealthy, router can fallback according to config.
6. When evaluator fails, router still serves requests using configured default difficulty.
7. Structured logs show request ID, difficulty, selected model, and fallback hops.
8. Streaming works for downstream models in at least one integration test.
9. A dockerized deployment works with mounted config and env vars.
10. Automated tests cover the main happy paths and key failure paths.

---

## 21. Nice-to-have later

Not required for v1:

* distributed Redis-backed rate limiting
* weighted load balancing among equivalent models
* cost-aware routing
* latency-aware routing
* per-tenant quotas
* admin UI
* request/response caching
* learning-based router
* Responses API compatibility in addition to Chat Completions

---

## 22. Notes for Codex

Implementation guidance:

* prefer small, testable classes
* keep provider-specific logic isolated in client layer
* keep routing pure where possible
* ensure all semaphore acquisitions are released in `finally`
* do not trust evaluator output
* treat streaming as a separate code path
* prioritize correctness and observability over premature optimization
* write tests alongside implementation, not after

Suggested order:

1. config
2. schemas
3. single upstream client
4. basic proxy route
5. evaluator
6. routing
7. rate limits
8. fallback
9. metrics/logging
10. streaming
11. tests
12. containerization