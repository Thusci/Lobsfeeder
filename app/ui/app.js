const statusValue = document.getElementById("status-value");
const statusMeta = document.getElementById("status-meta");
const opsOutput = document.getElementById("ops-output");
const chatOutput = document.getElementById("chat-output");
const configOutput = document.getElementById("config-output");
const providerCards = document.getElementById("provider-cards");
const modelsSummary = document.getElementById("models-summary");
const editorState = document.getElementById("editor-state");
const providerCreator = document.getElementById("provider-creator");
const providerNameInput = document.getElementById("provider-name-input");
const providerTypeInput = document.getElementById("provider-type-input");
const modelsSaveButton = document.getElementById("btn-models-save");
const modelsValidateButton = document.getElementById("btn-models-validate");
const discardDraftButton = document.getElementById("btn-discard-draft");

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
const configJsonInput = document.getElementById("config-json");
const providerState = new Map();
let currentConfig = null;
let currentConfigSource = "unknown";
let lastLoadedConfigJson = "";
let hasUnsavedChanges = false;
const PROVIDER_OPTIONS = ["openai_compatible", "openai-codex-oauth"];

document.getElementById("btn-refresh").addEventListener("click", refreshStatus);
document.getElementById("btn-health").addEventListener("click", () => callOps("/healthz"));
document.getElementById("btn-ready").addEventListener("click", () => callOps("/readyz"));
document.getElementById("btn-metrics").addEventListener("click", () => callOps("/metrics"));
document.getElementById("btn-debug").addEventListener("click", () => callOps("/debug/models"));
document.getElementById("btn-config-load").addEventListener("click", loadConfig);
document.getElementById("btn-config-validate").addEventListener("click", validateConfig);
document.getElementById("btn-config-save").addEventListener("click", saveConfig);
document.getElementById("btn-models-validate").addEventListener("click", validateFromCards);
document.getElementById("btn-models-save").addEventListener("click", saveFromCards);
document.getElementById("btn-provider-add").addEventListener("click", showProviderCreator);
document.getElementById("btn-provider-create").addEventListener("click", addProvider);
document.getElementById("btn-provider-cancel").addEventListener("click", hideProviderCreator);
document.getElementById("btn-models-load").addEventListener("click", loadModels);
discardDraftButton.addEventListener("click", discardDraft);

document.getElementById("btn-send").addEventListener("click", sendChat);
document.getElementById("btn-stream").addEventListener("click", streamChat);
document.getElementById("btn-reset").addEventListener("click", resetTemplate);
configJsonInput.addEventListener("input", handleConfigTextareaInput);
window.addEventListener("beforeunload", guardUnsavedChanges);

resetTemplate();
refreshStatus();
updateEditorActions();
setEditorState("Load config to start editing", "ready");
loadModels();

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

async function loadConfig() {
  configOutput.textContent = "Loading config...";
  try {
    const data = await callJson("/admin/config");
    currentConfigSource = data.source || "unknown";
    currentConfig = data.config;
    applyLoadedConfig(currentConfig);
    configOutput.textContent = buildConfigStatus(`Loaded from ${currentConfigSource}.`);
    renderProviderCards(currentConfig);
  } catch (err) {
    configOutput.textContent = String(err.message || err);
  }
}

async function loadModels() {
  updateModelsSummary("Loading models...");
  try {
    const data = await callJson("/admin/config");
    currentConfigSource = data.source || "unknown";
    currentConfig = data.config;
    applyLoadedConfig(currentConfig);
    renderProviderCards(currentConfig);
    updateModelsSummary(`Loaded ${countModels(currentConfig)} models from ${currentConfigSource}.`);
    setEditorState("Config loaded", "ready");
  } catch (err) {
    updateModelsSummary(String(err.message || err));
    providerCards.innerHTML = "";
    setEditorState("Load failed", "error");
  }
}

async function validateConfig() {
  configOutput.textContent = "Validating...";
  try {
    const payload = parseJsonObject(configJsonInput.value, "config");
    await callJsonWithBody("/admin/config/validate", payload);
    configOutput.textContent = buildConfigStatus("Config is valid.");
    setEditorState("Validation passed", "success");
  } catch (err) {
    configOutput.textContent = String(err.message || err);
    setEditorState("Validation failed", "error");
  }
}

async function saveConfig() {
  configOutput.textContent = "Saving...";
  try {
    const payload = parseJsonObject(configJsonInput.value, "config");
    await callJsonWithBody("/admin/config", payload, "PUT");
    currentConfig = payload;
    renderProviderCards(currentConfig);
    currentConfigSource = "db";
    markPersisted();
    configOutput.textContent = buildConfigStatus("Config saved and applied.");
    updateModelsSummary("Saved changes to DB.");
    setEditorState("Saved to DB", "success");
  } catch (err) {
    configOutput.textContent = String(err.message || err);
    setEditorState("Save failed", "error");
  }
}

async function validateFromCards() {
  syncConfigFromTextareaIfNeeded();
  await validateConfig();
}

async function saveFromCards() {
  syncConfigFromTextareaIfNeeded();
  if (currentConfigSource !== "db") {
    configOutput.textContent = buildConfigStatus(
      "Current config source is file. Switch server.config_source to db and restart Docker before saving."
    );
    updateModelsSummary("Current source is file; edits are not yet persistent.");
    setEditorState("DB mode required", "warning");
    return;
  }
  await saveConfig();
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

function parseJsonObject(value, field) {
  try {
    const parsed = JSON.parse(value);
    if (parsed === null || typeof parsed !== "object" || Array.isArray(parsed)) {
      throw new Error(`${field} must be a JSON object`);
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

async function callJsonWithBody(path, payload, method = "POST") {
  const base = resolveBaseUrl();
  const url = `${base}${path}`;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), getTimeout());
  try {
    const response = await fetch(url, {
      method,
      headers: buildHeaders(),
      body: JSON.stringify(payload),
      signal: controller.signal,
    });
    const text = await response.text();
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${text}`);
    }
    return text ? JSON.parse(text) : {};
  } finally {
    clearTimeout(timeout);
  }
}

function countModels(config) {
  if (!config || !config.models) return 0;
  return Object.keys(config.models).length;
}

function renderProviderCards(config) {
  providerCards.innerHTML = "";
  if (!config || !config.models) {
    updateModelsSummary("No models found in config.");
    return;
  }

  const models = Object.entries(config.models).map(([name, model]) => ({
    name,
    model,
    providerGroup: getProviderGroupName(model),
  }));

  const grouped = new Map();
  models.forEach((entry) => {
    if (!grouped.has(entry.providerGroup)) grouped.set(entry.providerGroup, []);
    grouped.get(entry.providerGroup).push(entry);
  });

  const providers = Array.from(grouped.entries()).sort((a, b) => a[0].localeCompare(b[0]));
  providers.forEach(([provider, items]) => {
    items.sort((a, b) => a.name.localeCompare(b.name));
    providerCards.appendChild(buildProviderSection(provider, items));
  });

  const providerCount = providers.length;
  updateModelsSummary(`Providers: ${providerCount} | Models: ${models.length}`);
}

function buildProviderSection(provider, models) {
  const section = document.createElement("section");
  section.className = "provider-section";

  const header = document.createElement("div");
  header.className = "provider-header";

  const toggle = document.createElement("button");
  toggle.type = "button";
  toggle.className = "provider-toggle";
  toggle.setAttribute("aria-expanded", "true");

  const title = document.createElement("div");
  title.className = "provider-title";
  title.textContent = provider;

  const meta = document.createElement("div");
  meta.className = "provider-meta";
  meta.textContent = `${models.length} models`;

  toggle.appendChild(title);
  toggle.appendChild(meta);
  header.appendChild(toggle);

  const actions = document.createElement("div");
  actions.className = "provider-actions";

  const addModelButton = document.createElement("button");
  addModelButton.type = "button";
  addModelButton.className = "mini-btn";
  addModelButton.textContent = "Add Model";
  addModelButton.addEventListener("click", (event) => {
    event.stopPropagation();
    toggleModelCreator(section, provider);
  });

  const deleteProviderButton = document.createElement("button");
  deleteProviderButton.type = "button";
  deleteProviderButton.className = "mini-btn danger";
  deleteProviderButton.textContent = "Delete Provider";
  deleteProviderButton.addEventListener("click", (event) => {
    event.stopPropagation();
    deleteProvider(provider);
  });

  actions.appendChild(addModelButton);
  actions.appendChild(deleteProviderButton);
  header.appendChild(actions);

  const content = document.createElement("div");
  content.className = "provider-content";

  const creator = buildModelCreator(provider, section);
  content.appendChild(creator);

  const grid = document.createElement("div");
  grid.className = "model-card-grid";
  models.forEach((entry) => {
    grid.appendChild(buildModelCard(entry.name, entry.model));
  });
  content.appendChild(grid);

  const isCollapsed = providerState.get(provider) === true;
  if (isCollapsed) {
    section.classList.add("collapsed");
    toggle.setAttribute("aria-expanded", "false");
  }

  toggle.addEventListener("click", () => {
    const nowCollapsed = !section.classList.contains("collapsed");
    section.classList.toggle("collapsed");
    providerState.set(provider, nowCollapsed);
    toggle.setAttribute("aria-expanded", nowCollapsed ? "false" : "true");
  });

  section.appendChild(header);
  section.appendChild(content);
  return section;
}

function buildModelCard(name, model) {
  const card = document.createElement("article");
  card.className = "model-card";

  const header = document.createElement("div");
  header.className = "model-card-header";

  const surface = document.createElement("div");
  surface.className = "model-card-surface";

  const title = document.createElement("input");
  title.className = "model-title";
  title.type = "text";
  title.value = name;
  title.addEventListener("change", () => renameModel(name, title.value.trim()));

  const subtitle = document.createElement("div");
  subtitle.className = "model-sub";
  subtitle.textContent = `group: ${safeText(getProviderGroupName(model))} | type: ${safeText(model && model.provider)}`;

  const titleWrap = document.createElement("div");
  titleWrap.className = "model-title-wrap";
  titleWrap.appendChild(title);
  titleWrap.appendChild(subtitle);
  header.appendChild(titleWrap);

  const chips = document.createElement("div");
  chips.className = "model-chips";
  chips.appendChild(createChip(model && model.upstream_model_name ? "Upstream Ready" : "Upstream Missing"));
  chips.appendChild(createChip(`Timeout ${safeText(model && model.timeout_seconds)}s`, "accent"));
  header.appendChild(chips);

  const deleteButton = document.createElement("button");
  deleteButton.type = "button";
  deleteButton.className = "mini-btn danger";
  deleteButton.textContent = "Delete";
  deleteButton.addEventListener("click", () => deleteModel(name));
  header.appendChild(deleteButton);

  const body = document.createElement("div");
  body.className = "model-stack";
  body.appendChild(
    createFieldGroup("Identity", [
      createBoundField(name, "provider_group", getProviderGroupName(model), { label: "Provider Group" }),
      createBoundField(name, "provider", model && model.provider, {
        rerender: true,
        label: "Provider Type",
        type: "select",
        choices: PROVIDER_OPTIONS,
      }),
      createBoundField(name, "upstream_model_name", model && model.upstream_model_name, { label: "Upstream Model" }),
    ])
  );
  body.appendChild(
    createFieldGroup("Endpoint", [
      createBoundField(name, "base_url", model && model.base_url, { label: "Base URL", fullWidth: true }),
      createBoundField(name, "api_key", model && model.api_key, {
        type: "password",
        label: "API Key",
        fullWidth: true,
        hidden: model && model.provider === "openai-codex-oauth",
      }),
      createBoundField(name, "oauth_token_path", model && model.oauth_token_path, {
        label: "OAuth Token Path",
        fullWidth: true,
        placeholder: "~/.codex/auth.json",
        hidden: model && model.provider !== "openai-codex-oauth",
      }),
      createBoundField(name, "timeout_seconds", model && model.timeout_seconds, { type: "number", label: "Timeout Seconds" }),
    ])
  );
  body.appendChild(
    createFieldGroup("Retry", [
      createBoundField(name, "retry.max_attempts", model && model.retry && model.retry.max_attempts, {
        type: "number",
        label: "Max Attempts",
      }),
      createBoundField(name, "retry.backoff_initial_ms", model && model.retry && model.retry.backoff_initial_ms, {
        type: "number",
        label: "Initial Backoff",
      }),
      createBoundField(name, "retry.backoff_max_ms", model && model.retry && model.retry.backoff_max_ms, {
        type: "number",
        label: "Max Backoff",
      }),
    ])
  );
  body.appendChild(
    createFieldGroup("Limits", [
      createBoundField(name, "limits.rpm", model && model.limits && model.limits.rpm, { type: "number", label: "RPM" }),
      createBoundField(name, "limits.tpm", model && model.limits && model.limits.tpm, { type: "number", label: "TPM" }),
      createBoundField(name, "limits.concurrency", model && model.limits && model.limits.concurrency, {
        type: "number",
        label: "Concurrency",
      }),
    ])
  );
  body.appendChild(
    createFieldGroup("Health", [
      createBoundField(name, "health.failure_threshold", model && model.health && model.health.failure_threshold, {
        type: "number",
        label: "Failure Threshold",
      }),
      createBoundField(name, "health.cooldown_seconds", model && model.health && model.health.cooldown_seconds, {
        type: "number",
        label: "Cooldown Seconds",
      }),
    ])
  );

  surface.appendChild(header);
  surface.appendChild(body);
  card.appendChild(surface);
  return card;
}

function buildModelCreator(provider, section) {
  const wrap = document.createElement("div");
  wrap.className = "inline-creator hidden model-creator";

  const field = document.createElement("label");
  field.className = "field compact";

  const label = document.createElement("span");
  label.textContent = `New model for ${provider}`;

  const input = document.createElement("input");
  input.type = "text";
  input.placeholder = `${slugify(provider) || "model"}_new`;
  input.dataset.provider = provider;

  field.appendChild(label);
  field.appendChild(input);

  const actions = document.createElement("div");
  actions.className = "panel-actions";

  const createButton = document.createElement("button");
  createButton.type = "button";
  createButton.className = "btn";
  createButton.textContent = "Create Model";
  createButton.addEventListener("click", () => addModel(provider, input.value.trim()));

  const cancelButton = document.createElement("button");
  cancelButton.type = "button";
  cancelButton.className = "btn ghost";
  cancelButton.textContent = "Cancel";
  cancelButton.addEventListener("click", () => {
    input.value = "";
    wrap.classList.add("hidden");
    section.classList.remove("creating");
  });

  actions.appendChild(createButton);
  actions.appendChild(cancelButton);
  wrap.appendChild(field);
  wrap.appendChild(actions);
  return wrap;
}

function createBoundField(modelName, path, value, options = {}) {
  const label = document.createElement("label");
  label.className = "mini-field";
  if (options.fullWidth) {
    label.classList.add("full");
  }

  const span = document.createElement("span");
  span.textContent = options.label || path;

  let input;
  if (options.type === "select") {
    input = document.createElement("select");
    (options.choices || []).forEach((choice) => {
      const option = document.createElement("option");
      option.value = choice;
      option.textContent = choice;
      input.appendChild(option);
    });
    input.value = value === null || value === undefined ? "" : String(value);
    input.addEventListener("change", () => {
      applyFieldUpdate(modelName, path, input.value, options);
    });
  } else {
    input = document.createElement("input");
    input.type = options.type || "text";
    if (options.type === "number") {
      input.step = "1";
    }
    if (options.placeholder) {
      input.placeholder = options.placeholder;
    }
    input.value = value === null || value === undefined ? "" : String(value);
    input.addEventListener("input", () => {
      applyFieldUpdate(modelName, path, input.value, options);
    });
  }

  if (options.hidden) {
    label.classList.add("hidden");
  }

  label.appendChild(span);
  label.appendChild(input);
  return label;
}

function createFieldGroup(title, fields) {
  const group = document.createElement("section");
  group.className = "model-group";

  const heading = document.createElement("div");
  heading.className = "model-group-title";
  heading.textContent = title;

  const grid = document.createElement("div");
  grid.className = "model-form-grid";
  fields.forEach((field) => {
    grid.appendChild(field);
  });

  group.appendChild(heading);
  group.appendChild(grid);
  return group;
}

function createChip(text, tone = "default") {
  const chip = document.createElement("span");
  chip.className = `model-chip ${tone}`;
  chip.textContent = text;
  return chip;
}

function applyFieldUpdate(modelName, path, rawValue, options = {}) {
  if (!currentConfig || !currentConfig.models || !currentConfig.models[modelName]) {
    return;
  }

  const value = normalizeFieldValue(rawValue, options.type);
  setNestedValue(currentConfig.models[modelName], path, value);
  if (path === "provider") {
    applyProviderDefaults(currentConfig.models[modelName], value);
  }
  syncEditorFromConfig();
  updateModelsSummary(`Draft updated for ${modelName}.`);
  setEditorState(`Editing ${modelName}`, "dirty");

  if (options.rerender) {
    renderProviderCards(currentConfig);
  }
}

function ensureEditableConfig() {
  if (currentConfig && currentConfig.models) {
    return true;
  }

  try {
    const parsed = parseJsonObject(configJsonInput.value, "config");
    if (!parsed.models || typeof parsed.models !== "object") {
      parsed.models = {};
    }
    currentConfig = parsed;
    return true;
  } catch (err) {
    configOutput.textContent = String(err.message || err);
    return false;
  }
}

function addProvider() {
  if (!ensureEditableConfig()) return;
  const normalized = providerNameInput.value.trim();
  const providerType = providerTypeInput.value;
  if (!normalized) return;

  const hasProvider = Object.values(currentConfig.models).some((model) => (model && model.provider) === normalized);
  if (hasProvider) {
    updateModelsSummary(`Provider ${normalized} already exists.`);
    return;
  }

  const modelName = createUniqueModelName(slugify(normalized) || "model");
  currentConfig.models[modelName] = buildDefaultModel(normalized, providerType);
  syncEditorFromConfig();
  renderProviderCards(currentConfig);
  updateModelsSummary(`Added provider ${normalized} (${providerType}) with starter model ${modelName}.`);
  setEditorState(`Added provider ${normalized}`, "dirty");
  hideProviderCreator();
}

function addModel(provider, modelName) {
  if (!ensureEditableConfig()) return;
  if (!modelName) return;
  if (currentConfig.models[modelName]) {
    updateModelsSummary(`Model ${modelName} already exists.`);
    return;
  }

  const providerType = findProviderType(provider);
  currentConfig.models[modelName] = buildDefaultModel(provider, providerType);
  syncEditorFromConfig();
  providerState.set(provider, false);
  renderProviderCards(currentConfig);
  updateModelsSummary(`Added model ${modelName} to ${provider}.`);
  setEditorState(`Added model ${modelName}`, "dirty");
}

function deleteModel(modelName) {
  if (!ensureEditableConfig() || !currentConfig.models[modelName]) return;
  const references = collectModelReferences(modelName);
  if (references.length) {
    updateModelsSummary(`Cannot delete ${modelName}; still referenced by ${references.join(", ")}.`);
    return;
  }
  const confirmed = window.confirm(`Delete model ${modelName}?`);
  if (!confirmed) return;

  delete currentConfig.models[modelName];
  syncEditorFromConfig();
  renderProviderCards(currentConfig);
  updateModelsSummary(`Deleted model ${modelName}.`);
  setEditorState(`Deleted ${modelName}`, "dirty");
}

function deleteProvider(provider) {
  if (!ensureEditableConfig()) return;
  const modelNames = Object.entries(currentConfig.models)
    .filter(([, model]) => (model && model.provider) === provider)
    .map(([name]) => name);

  if (!modelNames.length) return;

  const referenced = modelNames.flatMap((name) => collectModelReferences(name).map((ref) => `${name}:${ref}`));
  if (referenced.length) {
    updateModelsSummary(`Cannot delete provider ${provider}; referenced models: ${referenced.join(", ")}.`);
    return;
  }

  const confirmed = window.confirm(`Delete provider ${provider} and its ${modelNames.length} models?`);
  if (!confirmed) return;

  modelNames.forEach((name) => {
    delete currentConfig.models[name];
  });
  syncEditorFromConfig();
  renderProviderCards(currentConfig);
  updateModelsSummary(`Deleted provider ${provider}.`);
  setEditorState(`Deleted provider ${provider}`, "dirty");
}

function renameModel(oldName, nextName) {
  if (!ensureEditableConfig() || !currentConfig.models[oldName]) return;
  if (!nextName || nextName === oldName) {
    renderProviderCards(currentConfig);
    return;
  }
  if (currentConfig.models[nextName]) {
    updateModelsSummary(`Model ${nextName} already exists.`);
    renderProviderCards(currentConfig);
    return;
  }

  currentConfig.models[nextName] = currentConfig.models[oldName];
  delete currentConfig.models[oldName];
  replaceModelReferences(oldName, nextName);
  syncEditorFromConfig();
  renderProviderCards(currentConfig);
  updateModelsSummary(`Renamed model ${oldName} to ${nextName}.`);
  setEditorState(`Renamed ${oldName}`, "dirty");
}

function buildDefaultModel(providerGroup, providerType = "openai_compatible") {
  const model = {
    provider: providerType,
    provider_group: providerGroup,
    base_url: "",
    api_key: providerType === "openai_compatible" ? "" : null,
    oauth_token_path: providerType === "openai-codex-oauth" ? "~/.codex/auth.json" : null,
    upstream_model_name: "",
    timeout_seconds: 60,
    retry: {
      max_attempts: 1,
      backoff_initial_ms: 500,
      backoff_max_ms: 2000,
    },
    limits: {
      rpm: 60,
      tpm: 60000,
      concurrency: 4,
    },
    health: {
      failure_threshold: 5,
      cooldown_seconds: 30,
    },
  };
  if (providerGroup === "openai") {
    model.base_url = "https://api.openai.com/v1";
  }
  return model;
}

function createUniqueModelName(baseName) {
  let candidate = baseName;
  let index = 1;
  while (currentConfig.models[candidate]) {
    candidate = `${baseName}_${index}`;
    index += 1;
  }
  return candidate;
}

function slugify(value) {
  return String(value)
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
}

function collectModelReferences(modelName) {
  if (!currentConfig || !currentConfig.routing) return [];

  const refs = [];
  const routing = currentConfig.routing;
  if (routing.evaluator_model === modelName) {
    refs.push("routing.evaluator_model");
  }

  const difficultyMap = routing.difficulty_to_model || {};
  Object.entries(difficultyMap).forEach(([difficulty, target]) => {
    if (target === modelName) {
      refs.push(`routing.difficulty_to_model.${difficulty}`);
    }
  });

  const ordered = (routing.fallback_policy && routing.fallback_policy.ordered_candidates) || {};
  Object.entries(ordered).forEach(([difficulty, candidates]) => {
    (candidates || []).forEach((candidate, index) => {
      if (candidate === modelName) {
        refs.push(`routing.fallback_policy.ordered_candidates.${difficulty}[${index}]`);
      }
    });
  });

  return refs;
}

function replaceModelReferences(oldName, nextName) {
  if (!currentConfig || !currentConfig.routing) return;

  const routing = currentConfig.routing;
  if (routing.evaluator_model === oldName) {
    routing.evaluator_model = nextName;
  }

  Object.keys(routing.difficulty_to_model || {}).forEach((difficulty) => {
    if (routing.difficulty_to_model[difficulty] === oldName) {
      routing.difficulty_to_model[difficulty] = nextName;
    }
  });

  const ordered = (routing.fallback_policy && routing.fallback_policy.ordered_candidates) || {};
  Object.keys(ordered).forEach((difficulty) => {
    ordered[difficulty] = (ordered[difficulty] || []).map((candidate) => (candidate === oldName ? nextName : candidate));
  });
}

function normalizeFieldValue(value, type) {
  if (value === "") return null;
  if (type === "number") {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return value;
}

function setNestedValue(target, path, value) {
  const parts = path.split(".");
  let cursor = target;
  for (let index = 0; index < parts.length - 1; index += 1) {
    const key = parts[index];
    if (!cursor[key] || typeof cursor[key] !== "object") {
      cursor[key] = {};
    }
    cursor = cursor[key];
  }

  cursor[parts[parts.length - 1]] = value;
}

function safeText(value) {
  if (value === null || value === undefined || value === "") return "--";
  return String(value);
}

function applyProviderDefaults(model, providerType) {
  if (!model) return;
  if (providerType === "openai-codex-oauth") {
    model.api_key = null;
    model.oauth_token_path = model.oauth_token_path || "~/.codex/auth.json";
    if (!model.base_url) {
      model.base_url = "https://api.openai.com/v1";
    }
    return;
  }

  model.oauth_token_path = null;
  model.api_key = model.api_key || "";
}

function buildConfigStatus(message) {
  return `${message}\nSource: ${currentConfigSource}. ${currentConfigSource === "db" ? "Edits can be persisted." : "Edits are read-only until you switch to db mode."}`;
}

function updateModelsSummary(message) {
  const sourceLabel = currentConfigSource === "unknown" ? "unknown" : currentConfigSource;
  const persistence =
    currentConfigSource === "db" ? "Persistent DB mode" : "File mode: refresh will discard unsaved edits";
  modelsSummary.textContent = `${message} | Source: ${sourceLabel} | ${persistence}`;
}

function syncConfigFromTextareaIfNeeded() {
  try {
    const parsed = parseJsonObject(configJsonInput.value, "config");
    currentConfig = parsed;
  } catch (_) {
    // Keep currentConfig untouched; validation/save will surface the parse error.
  }
}

function handleConfigTextareaInput() {
  syncConfigFromTextareaIfNeeded();
  hasUnsavedChanges = configJsonInput.value !== lastLoadedConfigJson;
  updateEditorActions();
  setEditorState(hasUnsavedChanges ? "JSON draft changed" : "Draft matches saved config", hasUnsavedChanges ? "dirty" : "ready");
}

function applyLoadedConfig(config) {
  currentConfig = config;
  configJsonInput.value = formatJson(currentConfig);
  lastLoadedConfigJson = configJsonInput.value;
  hasUnsavedChanges = false;
  updateEditorActions();
}

function syncEditorFromConfig() {
  configJsonInput.value = formatJson(currentConfig);
  hasUnsavedChanges = configJsonInput.value !== lastLoadedConfigJson;
  updateEditorActions();
}

function markPersisted() {
  lastLoadedConfigJson = formatJson(currentConfig);
  configJsonInput.value = lastLoadedConfigJson;
  hasUnsavedChanges = false;
  updateEditorActions();
}

function updateEditorActions() {
  modelsValidateButton.disabled = !currentConfig;
  modelsSaveButton.disabled = !currentConfig || !hasUnsavedChanges || currentConfigSource !== "db";
  discardDraftButton.disabled = !hasUnsavedChanges;
}

function setEditorState(message, tone = "ready") {
  editorState.textContent = message;
  editorState.dataset.tone = tone;
}

function showProviderCreator() {
  providerCreator.classList.remove("hidden");
  providerNameInput.focus();
}

function hideProviderCreator() {
  providerCreator.classList.add("hidden");
  providerNameInput.value = "";
  providerTypeInput.value = "openai_compatible";
}

function toggleModelCreator(section, provider) {
  const creator = section.querySelector(".model-creator");
  if (!creator) return;
  const input = creator.querySelector("input");
  const opening = creator.classList.contains("hidden");
  creator.classList.toggle("hidden");
  section.classList.toggle("creating", opening);
  if (opening && input) {
    input.focus();
  } else if (input) {
    input.value = "";
  }
  providerState.set(provider, false);
}

function findProviderType(providerGroup) {
  const model = Object.values((currentConfig && currentConfig.models) || {}).find(
    (item) => item && item.provider && getProviderGroupName(item) === providerGroup
  );
  return model && model.provider ? model.provider : "openai_compatible";
}

function getProviderGroupName(model) {
  return model && model.provider_group ? model.provider_group : model && model.provider ? model.provider : "unknown";
}

function discardDraft() {
  if (!hasUnsavedChanges || !lastLoadedConfigJson) return;
  const confirmed = window.confirm("Discard current draft and reload the last saved config?");
  if (!confirmed) return;
  configJsonInput.value = lastLoadedConfigJson;
  syncConfigFromTextareaIfNeeded();
  hasUnsavedChanges = false;
  renderProviderCards(currentConfig);
  updateEditorActions();
  setEditorState("Draft discarded", "ready");
}

function guardUnsavedChanges(event) {
  if (!hasUnsavedChanges) return;
  event.preventDefault();
  event.returnValue = "";
}
