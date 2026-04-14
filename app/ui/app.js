const statusValue = document.getElementById("status-value");
const statusMeta = document.getElementById("status-meta");
const opsOutput = document.getElementById("ops-output");
const chatOutput = document.getElementById("chat-output");

const baseUrlInput = document.getElementById("base-url");
const apiKeyInput = document.getElementById("api-key");
const requestIdInput = document.getElementById("request-id");
const timeoutInput = document.getElementById("timeout-ms");

const modelInput = document.getElementById("model");
const temperatureInput = document.getElementById("temperature");
const maxTokensInput = document.getElementById("max-tokens");
const streamFlag = document.getElementById("stream-flag");
const messagesInput = document.getElementById("messages");
const toolsInput = document.getElementById("tools");
const toolChoiceInput = document.getElementById("tool-choice");
const responseFormatInput = document.getElementById("response-format");

document.getElementById("btn-refresh").addEventListener("click", refreshStatus);
document.getElementById("btn-health").addEventListener("click", () => callOps("/healthz"));
document.getElementById("btn-ready").addEventListener("click", () => callOps("/readyz"));
document.getElementById("btn-metrics").addEventListener("click", () => callOps("/metrics"));
document.getElementById("btn-debug").addEventListener("click", () => callOps("/debug/models"));

document.getElementById("btn-send").addEventListener("click", sendChat);
document.getElementById("btn-stream").addEventListener("click", streamChat);
document.getElementById("btn-reset").addEventListener("click", resetTemplate);

resetTemplate();
refreshStatus();

function resolveBaseUrl() {
  const raw = baseUrlInput.value.trim();
  if (!raw) return "";
  return raw.replace(/\/$/, "");
}

function buildHeaders() {
  const headers = { "Content-Type": "application/json" };
  const apiKey = apiKeyInput.value.trim();
  if (apiKey) {
    headers["Authorization"] = `Bearer ${apiKey}`;
  }
  const requestId = requestIdInput.value.trim();
  if (requestId) {
    headers["X-Request-ID"] = requestId;
  }
  return headers;
}

function getTimeout() {
  const value = Number(timeoutInput.value);
  return Number.isFinite(value) ? value : 120000;
}

async function refreshStatus() {
  try {
    const ready = await callJson("/readyz", { quiet: true });
    statusValue.textContent = ready.ready ? "Ready" : "Not Ready";
    statusMeta.textContent = `Ready: ${ready.ready} | Models: ${ready.models}`;
    statusValue.style.color = ready.ready ? "#7bff9e" : "#f2b705";
  } catch (err) {
    statusValue.textContent = "Error";
    statusMeta.textContent = String(err.message || err);
    statusValue.style.color = "#f56b6b";
  }
}

async function callOps(path) {
  opsOutput.textContent = "Loading...";
  try {
    const data = await callJson(path);
    opsOutput.textContent = formatJson(data);
  } catch (err) {
    opsOutput.textContent = String(err.message || err);
  }
}

async function callJson(path, options = {}) {
  const base = resolveBaseUrl();
  const url = `${base}${path}`;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), getTimeout());
  try {
    const response = await fetch(url, {
      method: "GET",
      headers: buildHeaders(),
      signal: controller.signal,
    });
    const text = await response.text();
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${text}`);
    }
    if (options.raw) return text;
    return text ? JSON.parse(text) : {};
  } finally {
    clearTimeout(timeout);
  }
}

async function sendChat() {
  chatOutput.textContent = "Sending...";
  try {
    const payload = buildChatPayload(false);
    const response = await fetch(`${resolveBaseUrl()}/v1/chat/completions`, {
      method: "POST",
      headers: buildHeaders(),
      body: JSON.stringify(payload),
    });
    const text = await response.text();
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${text}`);
    }
    chatOutput.textContent = formatJson(JSON.parse(text));
  } catch (err) {
    chatOutput.textContent = String(err.message || err);
  }
}

async function streamChat() {
  chatOutput.textContent = "Streaming...";
  try {
    const payload = buildChatPayload(true);
    const response = await fetch(`${resolveBaseUrl()}/v1/chat/completions`, {
      method: "POST",
      headers: buildHeaders(),
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      const text = await response.text();
      throw new Error(`HTTP ${response.status}: ${text}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      chatOutput.textContent = buffer;
    }
  } catch (err) {
    chatOutput.textContent = String(err.message || err);
  }
}

function buildChatPayload(forceStream) {
  const messages = parseJsonArray(messagesInput.value, "messages");
  const tools = toolsInput.value.trim() ? parseJsonArray(toolsInput.value, "tools") : undefined;
  const toolChoice = parseJsonValue(toolChoiceInput.value.trim());
  const responseFormat = parseJsonValue(responseFormatInput.value.trim());

  return {
    model: modelInput.value.trim() || "auto",
    messages,
    temperature: Number(temperatureInput.value || 0.7),
    max_tokens: Number(maxTokensInput.value || 256),
    stream: forceStream || streamFlag.value === "true",
    tools,
    tool_choice: toolChoice,
    response_format: responseFormat,
  };
}

function parseJsonArray(value, field) {
  try {
    const parsed = JSON.parse(value);
    if (!Array.isArray(parsed)) {
      throw new Error(`${field} must be a JSON array`);
    }
    return parsed;
  } catch (err) {
    throw new Error(`${field} parse error: ${err.message || err}`);
  }
}

function parseJsonValue(value) {
  if (!value) return undefined;
  if (value === "auto") return "auto";
  try {
    return JSON.parse(value);
  } catch (_) {
    return value;
  }
}

function resetTemplate() {
  messagesInput.value = JSON.stringify(
    [
      { role: "system", content: "You are a helpful assistant." },
      { role: "user", content: "Give me a one-line status update." },
    ],
    null,
    2
  );
  toolsInput.value = "[]";
  toolChoiceInput.value = "";
  responseFormatInput.value = "";
}

function formatJson(data) {
  return JSON.stringify(data, null, 2);
}
