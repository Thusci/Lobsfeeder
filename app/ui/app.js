const STORAGE_KEYS = {
  language: "lobsfeeder.ui.language",
  baseUrl: "lobsfeeder.ui.baseUrl",
  timeout: "lobsfeeder.ui.timeout",
};

const PROVIDER_OPTIONS = ["openai_compatible", "openai-codex-oauth"];

const STRINGS = {
  en: {
    "document.title": "Lobsfeeder Control Console",
    "hero.eyebrow": "Lobsfeeder",
    "hero.title": "Control Console",
    "hero.subhead": "Route, probe, and debug your gateway without leaving the browser.",
    "hero.disclaimer": "Independent project. Not affiliated with the official OpenClaw project.",
    "hero.languageSwitch": "Language switch",
    "status.label": "Status",
    "status.unknown": "Unknown",
    "status.ready": "Ready",
    "status.notReady": "Not Ready",
    "status.error": "Error",
    "status.meta": "Ready: {ready} | Models: {models}",
    "connection.title": "Connection",
    "connection.copy": "Configure the router endpoint used by the browser console.",
    "connection.baseUrl": "Base URL",
    "connection.baseUrlPlaceholder": "Leave empty for same origin",
    "connection.routerKey": "Router API Key",
    "connection.routerKeyPlaceholder": "Raw key or Bearer token",
    "connection.requestId": "X-Request-ID",
    "connection.timeout": "Timeout (ms)",
    "admin.title": "Admin Access",
    "admin.copy": "Unlock the management panels before loading or editing router configuration.",
    "admin.keyLabel": "Admin API Key",
    "admin.keyPlaceholder": "Use admin key, or leave empty to probe open admin routes",
    "admin.unlock": "Unlock Admin",
    "admin.lock": "Lock",
    "admin.statusLocked": "Locked",
    "admin.statusUnlocked": "Unlocked",
    "admin.noteLocked": "Unlock the admin area to manage config and providers.",
    "admin.noteUnlocked": "Admin access unlocked. Management panels are ready.",
    "admin.noteUnlocking": "Checking admin access...",
    "admin.noteUnauthorized": "Admin auth rejected. Check the admin key or router key.",
    "admin.noteProbe": "If admin routes are open, you can leave the admin key empty and click unlock.",
    "admin.configLocked": "Unlock admin access before managing configuration.",
    "admin.modelsLocked": "Unlock admin access before editing providers and models.",
    "ops.title": "Router Ops",
    "ops.copy": "Probe health, readiness, metrics, and model debug endpoints.",
    "ops.outputIdle": "Click a button to query the router.",
    "ops.loading": "Loading...",
    "config.title": "Config Manager (DB)",
    "config.copy": "Load, validate, and save the active router configuration.",
    "config.saveApply": "Save + Apply",
    "config.jsonLabel": "Config JSON",
    "config.outputDefault": "Admin config not loaded.",
    "config.loading": "Loading config...",
    "config.validating": "Validating...",
    "config.saving": "Saving...",
    "config.valid": "Config is valid.",
    "config.saved": "Config saved and applied.",
    "config.loaded": "Loaded from {source}.",
    "config.warning": "Warning: {warning}",
    "config.sourceLine": "Source: {source}. {persistence}",
    "config.persistenceDb": "Edits can be persisted.",
    "config.persistenceFile": "Edits are read-only until you switch to db mode.",
    "config.dbModeRequired": "Current config source is file. Switch server.config_source to db and restart Docker before saving.",
    "models.title": "Providers & Models",
    "models.copy": "Edit providers, model endpoints, auth, limits, and health settings.",
    "models.validateEdits": "Validate Edits",
    "models.saveToDb": "Save To DB",
    "models.newProvider": "New Provider",
    "models.loadFromDb": "Load From DB",
    "models.discardDraft": "Discard Draft",
    "models.providerGroupName": "Provider Group Name",
    "models.providerGroupPlaceholder": "openai_compatible",
    "models.providerType": "Provider Type",
    "models.createProvider": "Create Provider",
    "models.summaryLocked": "Unlock admin access to load providers.",
    "models.summaryLoading": "Loading models...",
    "models.summaryNone": "No models found in config.",
    "models.summaryProviders": "Providers: {providers} | Models: {models}",
    "models.summaryLoaded": "Loaded {count} models from {source}.",
    "models.summarySaved": "Saved changes to DB.",
    "models.summaryFileOnly": "Current source is file; edits are not yet persistent.",
    "models.summaryDraftUpdated": "Draft updated for {model}.",
    "models.summaryProviderExists": "Provider group {provider} already exists.",
    "models.summaryModelExists": "Model {model} already exists.",
    "models.summaryProviderAdded": "Added provider group {provider} ({providerType}) with starter model {model}.",
    "models.summaryModelAdded": "Added model {model} to {provider}.",
    "models.summaryDeleteModelBlocked": "Cannot delete {model}; still referenced by {refs}.",
    "models.summaryDeleteProviderBlocked": "Cannot delete provider {provider}; referenced models: {refs}.",
    "models.summaryModelDeleted": "Deleted model {model}.",
    "models.summaryProviderDeleted": "Deleted provider {provider}.",
    "models.summaryModelRenamed": "Renamed model {oldName} to {newName}.",
    "models.summaryLoadFailed": "Load failed: {message}",
    "models.addModel": "Add Model",
    "models.deleteProvider": "Delete Provider",
    "models.deleteModel": "Delete",
    "models.newModelFor": "New model for {provider}",
    "models.createModel": "Create Model",
    "models.identity": "Identity",
    "models.endpoint": "Endpoint",
    "models.retry": "Retry",
    "models.limits": "Limits",
    "models.health": "Health",
    "models.providerGroup": "Provider Group",
    "models.providerKind": "Provider Type",
    "models.upstreamModel": "Upstream Model",
    "models.baseUrl": "Base URL",
    "models.apiKey": "API Key",
    "models.apiKeyHeader": "API Key Header",
    "models.apiKeyPrefix": "API Key Prefix",
    "models.oauthTokenPath": "OAuth Token Path",
    "models.timeoutSeconds": "Timeout Seconds",
    "models.maxAttempts": "Max Attempts",
    "models.initialBackoff": "Initial Backoff",
    "models.maxBackoff": "Max Backoff",
    "models.rpm": "RPM",
    "models.tpm": "TPM",
    "models.concurrency": "Concurrency",
    "models.failureThreshold": "Failure Threshold",
    "models.cooldownSeconds": "Cooldown Seconds",
    "models.upstreamReady": "Upstream Ready",
    "models.upstreamMissing": "Upstream Missing",
    "models.timeoutChip": "Timeout {seconds}s",
    "models.providerMeta": "{count} models",
    "models.modelSubtitle": "group: {group} | type: {provider}",
    "chat.title": "Chat Completions",
    "chat.copy": "Send regular or streaming OpenAI-compatible chat requests through the router.",
    "chat.send": "Send",
    "chat.stream": "Stream",
    "chat.resetTemplate": "Reset Template",
    "chat.model": "Model",
    "chat.temperature": "Temperature",
    "chat.maxTokens": "Max Tokens",
    "chat.streamMode": "Stream",
    "chat.messages": "Messages (JSON array)",
    "chat.tools": "Tools (optional JSON array)",
    "chat.toolsPlaceholder": "[]",
    "chat.toolChoice": "Tool Choice (optional JSON or string)",
    "chat.toolChoicePlaceholder": "auto",
    "chat.responseFormat": "Response Format (optional JSON)",
    "chat.responseFormatPlaceholder": '{"type":"json_object"}',
    "chat.outputReady": "Ready.",
    "chat.sending": "Sending...",
    "chat.streaming": "Streaming...",
    "chat.sample.system": "You are a helpful assistant.",
    "chat.sample.user": "Give me a one-line status update.",
    "editor.locked": "Unlock admin access to start editing",
    "editor.ready": "Config loaded",
    "editor.warning": "Loaded with recovery warning",
    "editor.validationPassed": "Validation passed",
    "editor.validationFailed": "Validation failed",
    "editor.saved": "Saved to DB",
    "editor.dbRequired": "DB mode required",
    "editor.jsonChanged": "JSON draft changed",
    "editor.jsonMatches": "Draft matches saved config",
    "editor.editing": "Editing {model}",
    "editor.addedProvider": "Added provider group {provider}",
    "editor.addedModel": "Added model {model}",
    "editor.deletedModel": "Deleted {model}",
    "editor.deletedProvider": "Deleted provider {provider}",
    "editor.renamedModel": "Renamed {model}",
    "editor.discarded": "Draft discarded",
    "common.refresh": "Refresh Status",
    "common.load": "Load",
    "common.validate": "Validate",
    "common.cancel": "Cancel",
    "common.optional": "Optional",
    "common.true": "True",
    "common.false": "False",
    "common.yes": "Yes",
    "common.no": "No",
    "common.none": "--",
    "source.unknown": "unknown",
    "source.file": "file",
    "source.db": "db",
    "source.fileFallback": "file-fallback",
    "confirm.deleteModel": "Delete model {model}?",
    "confirm.deleteProvider": "Delete provider group {provider} and its {count} models?",
    "confirm.discardDraft": "Discard current draft and reload the last saved config?",
    "error.timeout": "Request timed out after {ms} ms.",
    "error.jsonArray": "{field} must be a JSON array: {message}",
    "error.jsonObject": "{field} must be a JSON object: {message}",
    "field.messages": "Messages",
    "field.tools": "Tools",
    "field.config": "Config",
    "leave.unsaved": "You have unsaved changes.",
  },
  zh: {
    "document.title": "Lobsfeeder 控制台",
    "hero.eyebrow": "Lobsfeeder",
    "hero.title": "控制台",
    "hero.subhead": "直接在浏览器里完成路由探测、调试和配置管理。",
    "hero.disclaimer": "独立社区项目，与 OpenClaw 官方项目没有关联。",
    "hero.languageSwitch": "语言切换",
    "status.label": "状态",
    "status.unknown": "未知",
    "status.ready": "就绪",
    "status.notReady": "未就绪",
    "status.error": "错误",
    "status.meta": "就绪: {ready} | 模型数: {models}",
    "connection.title": "连接配置",
    "connection.copy": "配置浏览器控制台所使用的路由器地址和请求参数。",
    "connection.baseUrl": "基础地址",
    "connection.baseUrlPlaceholder": "留空表示当前同源地址",
    "connection.routerKey": "路由器 API Key",
    "connection.routerKeyPlaceholder": "原始 key 或 Bearer token",
    "connection.requestId": "X-Request-ID",
    "connection.timeout": "超时（毫秒）",
    "admin.title": "管理页访问",
    "admin.copy": "先解锁管理区域，再加载或编辑路由配置。",
    "admin.keyLabel": "管理 API Key",
    "admin.keyPlaceholder": "填写管理 key；如果管理接口开放，也可以留空直接探测",
    "admin.unlock": "解锁管理页",
    "admin.lock": "锁定",
    "admin.statusLocked": "已锁定",
    "admin.statusUnlocked": "已解锁",
    "admin.noteLocked": "请先解锁管理区，再进行配置和模型管理。",
    "admin.noteUnlocked": "管理访问已解锁，可以开始加载和编辑配置。",
    "admin.noteUnlocking": "正在检查管理访问权限...",
    "admin.noteUnauthorized": "管理鉴权失败，请检查管理 key 或路由器 key。",
    "admin.noteProbe": "如果管理接口未开启独立鉴权，可以留空后直接点击解锁。",
    "admin.configLocked": "请先解锁管理访问，再管理配置。",
    "admin.modelsLocked": "请先解锁管理访问，再编辑 provider 和模型。",
    "ops.title": "路由运维",
    "ops.copy": "检查健康状态、就绪状态、指标和模型调试端点。",
    "ops.outputIdle": "点击按钮查询路由器状态。",
    "ops.loading": "加载中...",
    "config.title": "配置管理（DB）",
    "config.copy": "加载、校验并保存当前生效的路由配置。",
    "config.saveApply": "保存并应用",
    "config.jsonLabel": "配置 JSON",
    "config.outputDefault": "尚未加载管理配置。",
    "config.loading": "正在加载配置...",
    "config.validating": "正在校验...",
    "config.saving": "正在保存...",
    "config.valid": "配置校验通过。",
    "config.saved": "配置已保存并应用。",
    "config.loaded": "已从 {source} 加载。",
    "config.warning": "警告：{warning}",
    "config.sourceLine": "来源：{source}。{persistence}",
    "config.persistenceDb": "当前修改可持久化保存。",
    "config.persistenceFile": "当前为文件模式，切换到 db 后才能持久化。",
    "config.dbModeRequired": "当前配置来源是 file。请把 server.config_source 改为 db 并重启后再保存。",
    "models.title": "Providers 与模型",
    "models.copy": "编辑 provider、模型端点、鉴权、限流和健康参数。",
    "models.validateEdits": "校验修改",
    "models.saveToDb": "保存到 DB",
    "models.newProvider": "新建 Provider",
    "models.loadFromDb": "从 DB 加载",
    "models.discardDraft": "放弃草稿",
    "models.providerGroupName": "Provider 分组名",
    "models.providerGroupPlaceholder": "openai_compatible",
    "models.providerType": "Provider 类型",
    "models.createProvider": "创建 Provider",
    "models.summaryLocked": "请先解锁管理访问，再加载 provider。",
    "models.summaryLoading": "正在加载模型...",
    "models.summaryNone": "当前配置中没有模型。",
    "models.summaryProviders": "Provider 数: {providers} | 模型数: {models}",
    "models.summaryLoaded": "已从 {source} 加载 {count} 个模型。",
    "models.summarySaved": "已将修改保存到 DB。",
    "models.summaryFileOnly": "当前来源是 file，修改暂时不会持久化。",
    "models.summaryDraftUpdated": "已更新 {model} 的草稿。",
    "models.summaryProviderExists": "Provider 分组 {provider} 已存在。",
    "models.summaryModelExists": "模型 {model} 已存在。",
    "models.summaryProviderAdded": "已添加 Provider 分组 {provider}（{providerType}），并创建初始模型 {model}。",
    "models.summaryModelAdded": "已向 {provider} 添加模型 {model}。",
    "models.summaryDeleteModelBlocked": "无法删除 {model}；它仍被这些位置引用：{refs}。",
    "models.summaryDeleteProviderBlocked": "无法删除 Provider 分组 {provider}；相关模型仍被引用：{refs}。",
    "models.summaryModelDeleted": "已删除模型 {model}。",
    "models.summaryProviderDeleted": "已删除 Provider 分组 {provider}。",
    "models.summaryModelRenamed": "已将模型 {oldName} 重命名为 {newName}。",
    "models.summaryLoadFailed": "加载失败：{message}",
    "models.addModel": "新增模型",
    "models.deleteProvider": "删除 Provider",
    "models.deleteModel": "删除",
    "models.newModelFor": "为 {provider} 新建模型",
    "models.createModel": "创建模型",
    "models.identity": "标识",
    "models.endpoint": "端点",
    "models.retry": "重试",
    "models.limits": "限流",
    "models.health": "健康",
    "models.providerGroup": "Provider 分组",
    "models.providerKind": "Provider 类型",
    "models.upstreamModel": "上游模型名",
    "models.baseUrl": "基础地址",
    "models.apiKey": "API Key",
    "models.apiKeyHeader": "API Key Header",
    "models.apiKeyPrefix": "API Key 前缀",
    "models.oauthTokenPath": "OAuth Token 路径",
    "models.timeoutSeconds": "超时秒数",
    "models.maxAttempts": "最大尝试次数",
    "models.initialBackoff": "初始退避",
    "models.maxBackoff": "最大退避",
    "models.rpm": "RPM",
    "models.tpm": "TPM",
    "models.concurrency": "并发",
    "models.failureThreshold": "失败阈值",
    "models.cooldownSeconds": "冷却秒数",
    "models.upstreamReady": "上游已配置",
    "models.upstreamMissing": "上游未配置",
    "models.timeoutChip": "超时 {seconds}s",
    "models.providerMeta": "{count} 个模型",
    "models.modelSubtitle": "group: {group} | type: {provider}",
    "chat.title": "Chat Completions",
    "chat.copy": "通过路由器发送普通或流式 OpenAI-compatible chat 请求。",
    "chat.send": "发送",
    "chat.stream": "流式发送",
    "chat.resetTemplate": "重置模板",
    "chat.model": "模型",
    "chat.temperature": "温度",
    "chat.maxTokens": "最大 Tokens",
    "chat.streamMode": "流式",
    "chat.messages": "Messages（JSON 数组）",
    "chat.tools": "Tools（可选 JSON 数组）",
    "chat.toolsPlaceholder": "[]",
    "chat.toolChoice": "Tool Choice（可选 JSON 或字符串）",
    "chat.toolChoicePlaceholder": "auto",
    "chat.responseFormat": "Response Format（可选 JSON）",
    "chat.responseFormatPlaceholder": '{"type":"json_object"}',
    "chat.outputReady": "已就绪。",
    "chat.sending": "发送中...",
    "chat.streaming": "流式接收中...",
    "chat.sample.system": "你是一个乐于助人的助手。",
    "chat.sample.user": "请给我一条简短的状态更新。",
    "editor.locked": "请先解锁管理访问，再开始编辑",
    "editor.ready": "配置已加载",
    "editor.warning": "已加载，但存在恢复告警",
    "editor.validationPassed": "校验通过",
    "editor.validationFailed": "校验失败",
    "editor.saved": "已保存到 DB",
    "editor.dbRequired": "需要 DB 模式",
    "editor.jsonChanged": "JSON 草稿已变化",
    "editor.jsonMatches": "草稿与已保存配置一致",
    "editor.editing": "正在编辑 {model}",
    "editor.addedProvider": "已添加 Provider 分组 {provider}",
    "editor.addedModel": "已添加模型 {model}",
    "editor.deletedModel": "已删除 {model}",
    "editor.deletedProvider": "已删除 Provider 分组 {provider}",
    "editor.renamedModel": "已重命名 {model}",
    "editor.discarded": "草稿已放弃",
    "common.refresh": "刷新状态",
    "common.load": "加载",
    "common.validate": "校验",
    "common.cancel": "取消",
    "common.optional": "可选",
    "common.true": "是",
    "common.false": "否",
    "common.yes": "是",
    "common.no": "否",
    "common.none": "--",
    "source.unknown": "unknown",
    "source.file": "file",
    "source.db": "db",
    "source.fileFallback": "file-fallback",
    "confirm.deleteModel": "确定删除模型 {model} 吗？",
    "confirm.deleteProvider": "确定删除 Provider 分组 {provider} 及其 {count} 个模型吗？",
    "confirm.discardDraft": "确定放弃当前草稿，并恢复到最近一次已加载的配置吗？",
    "error.timeout": "请求在 {ms} 毫秒后超时。",
    "error.jsonArray": "{field} 必须是 JSON 数组：{message}",
    "error.jsonObject": "{field} 必须是 JSON 对象：{message}",
    "field.messages": "Messages",
    "field.tools": "Tools",
    "field.config": "配置",
    "leave.unsaved": "当前有未保存修改。",
  },
};

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
const configLoadButton = document.getElementById("btn-config-load");
const configValidateButton = document.getElementById("btn-config-validate");
const configSaveButton = document.getElementById("btn-config-save");
const modelsLoadButton = document.getElementById("btn-models-load");
const providerAddButton = document.getElementById("btn-provider-add");
const providerCreateButton = document.getElementById("btn-provider-create");
const providerCancelButton = document.getElementById("btn-provider-cancel");
const sendButton = document.getElementById("btn-send");
const streamButton = document.getElementById("btn-stream");
const resetButton = document.getElementById("btn-reset");
const refreshButton = document.getElementById("btn-refresh");
const healthButton = document.getElementById("btn-health");
const readyButton = document.getElementById("btn-ready");
const metricsButton = document.getElementById("btn-metrics");
const debugButton = document.getElementById("btn-debug");
const adminUnlockButton = document.getElementById("btn-admin-unlock");
const adminLockButton = document.getElementById("btn-admin-lock");
const adminStatus = document.getElementById("admin-status");
const adminNote = document.getElementById("admin-note");
const adminApiKeyInput = document.getElementById("admin-api-key");
const configLockBanner = document.getElementById("config-lock-banner");
const modelsLockBanner = document.getElementById("models-lock-banner");
const adminPanels = Array.from(document.querySelectorAll(".admin-panel"));
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
const langButtons = Array.from(document.querySelectorAll("[data-lang]"));

const providerState = new Map();

const state = {
  language: loadStoredLanguage(),
  currentConfig: null,
  currentConfigSource: "unknown",
  currentConfigWritable: false,
  lastLoadedConfigJson: "",
  hasUnsavedChanges: false,
  adminUnlocked: false,
  status: { kind: "idle" },
  messages: {
    ops: { type: "localized", key: "ops.outputIdle" },
    chat: { type: "localized", key: "chat.outputReady" },
    config: { type: "localized", key: "config.outputDefault" },
    modelsSummary: { type: "localized", key: "models.summaryLocked" },
    adminNote: { type: "localized", key: "admin.noteLocked" },
    editor: { type: "localized", key: "editor.locked", tone: "warning" },
  },
};

const slotTargets = {
  ops: opsOutput,
  chat: chatOutput,
  config: configOutput,
  modelsSummary,
  adminNote,
  editor: editorState,
};

refreshButton.addEventListener("click", refreshStatus);
healthButton.addEventListener("click", () => callOps("/healthz"));
readyButton.addEventListener("click", () => callOps("/readyz"));
metricsButton.addEventListener("click", () => callOps("/metrics"));
debugButton.addEventListener("click", () => callOps("/debug/models"));
configLoadButton.addEventListener("click", loadConfig);
configValidateButton.addEventListener("click", validateConfig);
configSaveButton.addEventListener("click", saveConfig);
modelsValidateButton.addEventListener("click", validateFromCards);
modelsSaveButton.addEventListener("click", saveFromCards);
modelsLoadButton.addEventListener("click", loadModels);
providerAddButton.addEventListener("click", showProviderCreator);
providerCreateButton.addEventListener("click", addProvider);
providerCancelButton.addEventListener("click", hideProviderCreator);
discardDraftButton.addEventListener("click", discardDraft);
sendButton.addEventListener("click", sendChat);
streamButton.addEventListener("click", streamChat);
resetButton.addEventListener("click", resetTemplate);
adminUnlockButton.addEventListener("click", unlockAdmin);
adminLockButton.addEventListener("click", lockAdmin);
adminApiKeyInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    unlockAdmin();
  }
});
configJsonInput.addEventListener("input", handleConfigTextareaInput);
baseUrlInput.addEventListener("change", persistConnectionPrefs);
timeoutInput.addEventListener("change", persistConnectionPrefs);
window.addEventListener("beforeunload", guardUnsavedChanges);

langButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const nextLanguage = button.dataset.lang;
    if (!nextLanguage || nextLanguage === state.language) return;
    state.language = nextLanguage;
    localStorage.setItem(STORAGE_KEYS.language, nextLanguage);
    applyI18n();
  });
});

initialize();

function initialize() {
  restoreConnectionPrefs();
  resetTemplate();
  applyI18n();
  refreshStatus();
}

function loadStoredLanguage() {
  const stored = localStorage.getItem(STORAGE_KEYS.language);
  return stored === "zh" ? "zh" : "en";
}

function restoreConnectionPrefs() {
  const baseUrl = localStorage.getItem(STORAGE_KEYS.baseUrl);
  const timeout = localStorage.getItem(STORAGE_KEYS.timeout);
  if (baseUrl) {
    baseUrlInput.value = baseUrl;
  }
  if (timeout) {
    timeoutInput.value = timeout;
  }
}

function persistConnectionPrefs() {
  localStorage.setItem(STORAGE_KEYS.baseUrl, baseUrlInput.value.trim());
  localStorage.setItem(STORAGE_KEYS.timeout, String(getTimeout()));
}

function t(key, vars = {}) {
  const dictionary = STRINGS[state.language] || STRINGS.en;
  const template = dictionary[key] || STRINGS.en[key] || key;
  return template.replace(/\{(\w+)\}/g, (_, name) => {
    if (Object.prototype.hasOwnProperty.call(vars, name)) {
      return String(vars[name]);
    }
    return `{${name}}`;
  });
}

function applyI18n() {
  document.documentElement.lang = state.language;
  document.title = t("document.title");

  document.querySelectorAll("[data-i18n]").forEach((element) => {
    element.textContent = t(element.dataset.i18n);
  });

  document.querySelectorAll("[data-i18n-placeholder]").forEach((element) => {
    element.setAttribute("placeholder", t(element.dataset.i18nPlaceholder));
  });

  document.querySelectorAll("[data-i18n-aria-label]").forEach((element) => {
    element.setAttribute("aria-label", t(element.dataset.i18nAriaLabel));
  });

  langButtons.forEach((button) => {
    button.dataset.active = button.dataset.lang === state.language ? "true" : "false";
  });

  renderAllMessages();
  renderStatus();
  renderAdminAccess();
  if (state.currentConfig) {
    renderProviderCards(state.currentConfig);
  }
  updateEditorActions();
}

function renderAllMessages() {
  Object.keys(slotTargets).forEach(renderSlot);
}

function renderSlot(slot) {
  const target = slotTargets[slot];
  const message = state.messages[slot];
  if (!target || !message) return;
  target.textContent = resolveMessage(message);
  if (slot === "editor") {
    target.dataset.tone = message.tone || "ready";
  }
}

function resolveMessage(message) {
  if (!message) return "";
  if (message.type === "localized") {
    return t(message.key, message.vars || {});
  }
  return message.text;
}

function setLocalizedMessage(slot, key, vars = {}, extra = {}) {
  state.messages[slot] = { type: "localized", key, vars, tone: extra.tone };
  renderSlot(slot);
}

function setRawMessage(slot, text, extra = {}) {
  state.messages[slot] = { type: "raw", text, tone: extra.tone };
  renderSlot(slot);
}

function setStatus(nextStatus) {
  state.status = nextStatus;
  renderStatus();
}

function renderStatus() {
  if (state.status.kind === "ready") {
    statusValue.textContent = state.status.ready ? t("status.ready") : t("status.notReady");
    statusMeta.textContent = t("status.meta", {
      ready: state.status.ready ? t("common.yes") : t("common.no"),
      models: state.status.models,
    });
    statusValue.style.color = state.status.ready ? "#7bff9e" : "#f2b705";
    return;
  }

  if (state.status.kind === "error") {
    statusValue.textContent = t("status.error");
    statusMeta.textContent = state.status.message;
    statusValue.style.color = "#f56b6b";
    return;
  }

  statusValue.textContent = t("status.unknown");
  statusMeta.textContent = t("status.meta", {
    ready: t("common.none"),
    models: t("common.none"),
  });
  statusValue.style.color = "#f6f4f0";
}

function renderAdminAccess() {
  adminStatus.textContent = state.adminUnlocked ? t("admin.statusUnlocked") : t("admin.statusLocked");
  adminStatus.dataset.tone = state.adminUnlocked ? "unlocked" : "locked";

  adminPanels.forEach((panel) => {
    const locked = !state.adminUnlocked;
    panel.dataset.locked = locked ? "true" : "false";
    const guarded = panel.querySelector(".admin-guarded");
    if (guarded) {
      guarded.querySelectorAll("button, input, select, textarea").forEach((element) => {
        if (element === configJsonInput) {
          element.disabled = locked;
          return;
        }
        element.disabled = locked;
      });
    }
  });

  configLockBanner.classList.toggle("hidden", state.adminUnlocked);
  modelsLockBanner.classList.toggle("hidden", state.adminUnlocked);
}

function resolveBaseUrl() {
  const raw = baseUrlInput.value.trim();
  if (!raw) return "";
  return raw.replace(/\/$/, "");
}

function getTimeout() {
  const value = Number(timeoutInput.value);
  return Number.isFinite(value) ? value : 120000;
}

function resolveUrl(path) {
  return `${resolveBaseUrl()}${path}`;
}

function resolveScopedApiKey(scope) {
  if (scope === "admin") {
    return adminApiKeyInput.value.trim() || apiKeyInput.value.trim();
  }
  return apiKeyInput.value.trim();
}

function buildHeaders(scope = "router") {
  const headers = { "Content-Type": "application/json" };
  const apiKey = resolveScopedApiKey(scope);
  if (apiKey) {
    if (/^Bearer\s+/i.test(apiKey)) {
      headers.Authorization = apiKey;
    } else {
      headers.Authorization = `Bearer ${apiKey}`;
      headers["X-API-Key"] = apiKey;
    }
  }
  const requestId = requestIdInput.value.trim();
  if (requestId) {
    headers["X-Request-ID"] = requestId;
  }
  return headers;
}

function parseResponsePayload(text, contentType, responseType = "auto") {
  if (!text) {
    return responseType === "text" ? "" : {};
  }

  if (responseType === "text") {
    return text;
  }

  const normalizedType = String(contentType || "").toLowerCase();
  const expectsJson = responseType === "json" || normalizedType.includes("application/json");
  if (expectsJson) {
    return JSON.parse(text);
  }
  return text;
}

function extractErrorMessage(status, text) {
  if (!text) {
    return `HTTP ${status}`;
  }

  try {
    const parsed = JSON.parse(text);
    if (parsed && parsed.error && parsed.error.message) {
      return `HTTP ${status}: ${parsed.error.message}`;
    }
  } catch (_) {
    // Keep raw text.
  }

  return `HTTP ${status}: ${text}`;
}

function formatError(error) {
  if (error && error.name === "AbortError") {
    return t("error.timeout", { ms: getTimeout() });
  }
  return error && error.message ? error.message : String(error);
}

async function requestApi(path, options = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), getTimeout());
  const method = options.method || "GET";
  const scope = options.scope || "router";

  try {
    const response = await fetch(resolveUrl(path), {
      method,
      headers: buildHeaders(scope),
      body: options.body ? JSON.stringify(options.body) : undefined,
      signal: controller.signal,
    });
    const text = await response.text();
    if (!response.ok) {
      const error = new Error(extractErrorMessage(response.status, text));
      error.status = response.status;
      if (scope === "admin" && response.status === 401) {
        handleAdminUnauthorized();
      }
      throw error;
    }
    return parseResponsePayload(text, response.headers.get("content-type"), options.responseType);
  } finally {
    clearTimeout(timeout);
  }
}

function handleAdminUnauthorized() {
  state.adminUnlocked = false;
  setLocalizedMessage("adminNote", "admin.noteUnauthorized");
  setLocalizedMessage("modelsSummary", "models.summaryLocked");
  if (!state.currentConfig) {
    setLocalizedMessage("editor", "editor.locked", {}, { tone: "warning" });
  }
  renderAdminAccess();
  updateEditorActions();
}

async function refreshStatus() {
  try {
    const ready = await requestApi("/readyz");
    setStatus({
      kind: "ready",
      ready: Boolean(ready.ready),
      models: ready.models ?? t("common.none"),
    });
  } catch (error) {
    setStatus({ kind: "error", message: formatError(error) });
  }
}

async function callOps(path) {
  setLocalizedMessage("ops", "ops.loading");
  try {
    const data = await requestApi(path, {
      responseType: path === "/metrics" ? "text" : "auto",
    });
    setRawMessage("ops", typeof data === "string" ? data : formatJson(data));
  } catch (error) {
    setRawMessage("ops", formatError(error));
  }
}

async function unlockAdmin() {
  setLocalizedMessage("adminNote", "admin.noteUnlocking");
  setLocalizedMessage("config", "config.loading");
  try {
    const data = await requestApi("/admin/config", { scope: "admin" });
    state.adminUnlocked = true;
    renderAdminAccess();
    applyLoadedConfigPayload(data, { fromUnlock: true });
    setLocalizedMessage("adminNote", "admin.noteUnlocked");
  } catch (error) {
    setRawMessage("config", formatError(error));
    if (error.status !== 401) {
      setRawMessage("adminNote", formatError(error));
    }
  }
}

function lockAdmin() {
  state.adminUnlocked = false;
  renderAdminAccess();
  updateEditorActions();
  setLocalizedMessage("adminNote", "admin.noteLocked");
  if (!state.currentConfig) {
    setLocalizedMessage("modelsSummary", "models.summaryLocked");
    setLocalizedMessage("editor", "editor.locked", {}, { tone: "warning" });
  }
}

async function loadConfig() {
  if (!state.adminUnlocked) return;
  setLocalizedMessage("config", "config.loading");
  try {
    const data = await requestApi("/admin/config", { scope: "admin" });
    applyLoadedConfigPayload(data);
  } catch (error) {
    setRawMessage("config", formatError(error));
  }
}

async function loadModels() {
  if (!state.adminUnlocked) return;
  setLocalizedMessage("modelsSummary", "models.summaryLoading");
  try {
    const data = await requestApi("/admin/config", { scope: "admin" });
    applyLoadedConfigPayload(data);
  } catch (error) {
    setRawMessage("modelsSummary", t("models.summaryLoadFailed", { message: formatError(error) }));
  }
}

function applyLoadedConfigPayload(data, options = {}) {
  state.currentConfigSource = data.source || "unknown";
  state.currentConfigWritable = Boolean(data.writable);
  state.currentConfig = data.config;
  applyLoadedConfig(data.config);
  renderProviderCards(state.currentConfig);

  const sourceLabel = translateSource(state.currentConfigSource);
  const configStatus = buildConfigStatusText(t("config.loaded", { source: sourceLabel }), data.startup_warning);
  setRawMessage("config", configStatus);
  setLocalizedMessage("modelsSummary", "models.summaryLoaded", {
    count: countModels(state.currentConfig),
    source: sourceLabel,
  });
  setLocalizedMessage(
    "editor",
    data.startup_warning ? "editor.warning" : "editor.ready",
    {},
    { tone: data.startup_warning ? "warning" : "ready" }
  );

  if (options.fromUnlock && !data.startup_warning) {
    setLocalizedMessage("adminNote", "admin.noteUnlocked");
  }
}

async function validateConfig() {
  if (!state.adminUnlocked) return;
  setLocalizedMessage("config", "config.validating");
  try {
    const payload = parseJsonObject(configJsonInput.value, "field.config");
    await requestApi("/admin/config/validate", { method: "POST", body: payload, scope: "admin" });
    setRawMessage("config", buildConfigStatusText(t("config.valid")));
    setLocalizedMessage("editor", "editor.validationPassed", {}, { tone: "success" });
  } catch (error) {
    setRawMessage("config", formatError(error));
    setLocalizedMessage("editor", "editor.validationFailed", {}, { tone: "error" });
  }
}

async function saveConfig() {
  if (!state.adminUnlocked) return;
  setLocalizedMessage("config", "config.saving");
  try {
    const payload = parseJsonObject(configJsonInput.value, "field.config");
    await requestApi("/admin/config", { method: "PUT", body: payload, scope: "admin" });
    state.currentConfig = payload;
    state.currentConfigSource = "db";
    state.currentConfigWritable = true;
    renderProviderCards(state.currentConfig);
    markPersisted();
    setRawMessage("config", buildConfigStatusText(t("config.saved")));
    setLocalizedMessage("modelsSummary", "models.summarySaved");
    setLocalizedMessage("editor", "editor.saved", {}, { tone: "success" });
  } catch (error) {
    setRawMessage("config", formatError(error));
    setLocalizedMessage("editor", "editor.validationFailed", {}, { tone: "error" });
  }
}

async function validateFromCards() {
  syncConfigFromTextareaIfNeeded();
  await validateConfig();
}

async function saveFromCards() {
  syncConfigFromTextareaIfNeeded();
  if (!state.currentConfigWritable) {
    setRawMessage("config", buildConfigStatusText(t("config.dbModeRequired")));
    setLocalizedMessage("modelsSummary", "models.summaryFileOnly");
    setLocalizedMessage("editor", "editor.dbRequired", {}, { tone: "warning" });
    return;
  }
  await saveConfig();
}

async function sendChat() {
  setLocalizedMessage("chat", "chat.sending");
  try {
    const payload = buildChatPayload(false);
    const response = await requestApi("/v1/chat/completions", {
      method: "POST",
      body: payload,
    });
    setRawMessage("chat", formatJson(response));
  } catch (error) {
    setRawMessage("chat", formatError(error));
  }
}

async function streamChat() {
  setLocalizedMessage("chat", "chat.streaming");
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), getTimeout());
  try {
    const payload = buildChatPayload(true);
    const response = await fetch(resolveUrl("/v1/chat/completions"), {
      method: "POST",
      headers: buildHeaders("router"),
      body: JSON.stringify(payload),
      signal: controller.signal,
    });
    if (!response.ok) {
      const text = await response.text();
      throw new Error(extractErrorMessage(response.status, text));
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      setRawMessage("chat", buffer);
    }
  } catch (error) {
    setRawMessage("chat", formatError(error));
  } finally {
    clearTimeout(timeout);
  }
}

function buildChatPayload(forceStream) {
  const messages = parseJsonArray(messagesInput.value, "field.messages");
  const tools = toolsInput.value.trim() ? parseJsonArray(toolsInput.value, "field.tools") : undefined;
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

function parseJsonArray(value, fieldKey) {
  try {
    const parsed = JSON.parse(value);
    if (!Array.isArray(parsed)) {
      throw new Error(t("error.jsonArray", { field: t(fieldKey), message: "invalid type" }));
    }
    return parsed;
  } catch (error) {
    throw new Error(t("error.jsonArray", { field: t(fieldKey), message: error.message || error }));
  }
}

function parseJsonObject(value, fieldKey) {
  try {
    const parsed = JSON.parse(value);
    if (parsed === null || typeof parsed !== "object" || Array.isArray(parsed)) {
      throw new Error(t("error.jsonObject", { field: t(fieldKey), message: "invalid type" }));
    }
    return parsed;
  } catch (error) {
    throw new Error(t("error.jsonObject", { field: t(fieldKey), message: error.message || error }));
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
      { role: "system", content: t("chat.sample.system") },
      { role: "user", content: t("chat.sample.user") },
    ],
    null,
    2
  );
  toolsInput.value = "[]";
  toolChoiceInput.value = "";
  responseFormatInput.value = "";
  if (state.messages.chat.type === "localized") {
    setLocalizedMessage("chat", "chat.outputReady");
  }
}

function formatJson(data) {
  return JSON.stringify(data, null, 2);
}

function countModels(config) {
  if (!config || !config.models) return 0;
  return Object.keys(config.models).length;
}

function renderProviderCards(config) {
  providerCards.innerHTML = "";
  if (!config || !config.models) {
    setLocalizedMessage("modelsSummary", state.adminUnlocked ? "models.summaryNone" : "models.summaryLocked");
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

  setLocalizedMessage("modelsSummary", "models.summaryProviders", {
    providers: providers.length,
    models: models.length,
  });
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
  meta.textContent = t("models.providerMeta", { count: models.length });

  toggle.appendChild(title);
  toggle.appendChild(meta);
  header.appendChild(toggle);

  const actions = document.createElement("div");
  actions.className = "provider-actions";

  const addModelButton = document.createElement("button");
  addModelButton.type = "button";
  addModelButton.className = "mini-btn";
  addModelButton.textContent = t("models.addModel");
  addModelButton.addEventListener("click", (event) => {
    event.stopPropagation();
    toggleModelCreator(section, provider);
  });

  const deleteProviderButton = document.createElement("button");
  deleteProviderButton.type = "button";
  deleteProviderButton.className = "mini-btn danger";
  deleteProviderButton.textContent = t("models.deleteProvider");
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
  subtitle.textContent = t("models.modelSubtitle", {
    group: safeText(getProviderGroupName(model)),
    provider: safeText(model && model.provider),
  });

  const titleWrap = document.createElement("div");
  titleWrap.className = "model-title-wrap";
  titleWrap.appendChild(title);
  titleWrap.appendChild(subtitle);
  header.appendChild(titleWrap);

  const chips = document.createElement("div");
  chips.className = "model-chips";
  chips.appendChild(createChip(model && model.upstream_model_name ? t("models.upstreamReady") : t("models.upstreamMissing")));
  chips.appendChild(createChip(t("models.timeoutChip", { seconds: safeText(model && model.timeout_seconds) }), "accent"));
  header.appendChild(chips);

  const deleteButton = document.createElement("button");
  deleteButton.type = "button";
  deleteButton.className = "mini-btn danger";
  deleteButton.textContent = t("models.deleteModel");
  deleteButton.addEventListener("click", () => deleteModel(name));
  header.appendChild(deleteButton);

  const body = document.createElement("div");
  body.className = "model-stack";
  body.appendChild(
    createFieldGroup(t("models.identity"), [
      createBoundField(name, "provider_group", getProviderGroupName(model), { label: t("models.providerGroup") }),
      createBoundField(name, "provider", model && model.provider, {
        rerender: true,
        label: t("models.providerKind"),
        type: "select",
        choices: PROVIDER_OPTIONS,
      }),
      createBoundField(name, "upstream_model_name", model && model.upstream_model_name, { label: t("models.upstreamModel") }),
    ])
  );
  body.appendChild(
    createFieldGroup(t("models.endpoint"), [
      createBoundField(name, "base_url", model && model.base_url, { label: t("models.baseUrl"), fullWidth: true }),
      createBoundField(name, "api_key", model && model.api_key, {
        type: "password",
        label: t("models.apiKey"),
        fullWidth: true,
        hidden: model && model.provider === "openai-codex-oauth",
      }),
      createBoundField(name, "api_key_header", model && model.api_key_header, {
        label: t("models.apiKeyHeader"),
        hidden: model && model.provider === "openai-codex-oauth",
      }),
      createBoundField(name, "api_key_prefix", model && model.api_key_prefix, {
        label: t("models.apiKeyPrefix"),
        placeholder: "Bearer ",
        hidden: model && model.provider === "openai-codex-oauth",
      }),
      createBoundField(name, "oauth_token_path", model && model.oauth_token_path, {
        label: t("models.oauthTokenPath"),
        fullWidth: true,
        placeholder: "~/.codex/auth.json",
        hidden: model && model.provider !== "openai-codex-oauth",
      }),
      createBoundField(name, "timeout_seconds", model && model.timeout_seconds, { type: "number", label: t("models.timeoutSeconds") }),
    ])
  );
  body.appendChild(
    createFieldGroup(t("models.retry"), [
      createBoundField(name, "retry.max_attempts", model && model.retry && model.retry.max_attempts, {
        type: "number",
        label: t("models.maxAttempts"),
      }),
      createBoundField(name, "retry.backoff_initial_ms", model && model.retry && model.retry.backoff_initial_ms, {
        type: "number",
        label: t("models.initialBackoff"),
      }),
      createBoundField(name, "retry.backoff_max_ms", model && model.retry && model.retry.backoff_max_ms, {
        type: "number",
        label: t("models.maxBackoff"),
      }),
    ])
  );
  body.appendChild(
    createFieldGroup(t("models.limits"), [
      createBoundField(name, "limits.rpm", model && model.limits && model.limits.rpm, { type: "number", label: t("models.rpm") }),
      createBoundField(name, "limits.tpm", model && model.limits && model.limits.tpm, { type: "number", label: t("models.tpm") }),
      createBoundField(name, "limits.concurrency", model && model.limits && model.limits.concurrency, {
        type: "number",
        label: t("models.concurrency"),
      }),
    ])
  );
  body.appendChild(
    createFieldGroup(t("models.health"), [
      createBoundField(name, "health.failure_threshold", model && model.health && model.health.failure_threshold, {
        type: "number",
        label: t("models.failureThreshold"),
      }),
      createBoundField(name, "health.cooldown_seconds", model && model.health && model.health.cooldown_seconds, {
        type: "number",
        label: t("models.cooldownSeconds"),
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
  label.textContent = t("models.newModelFor", { provider });

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
  createButton.textContent = t("models.createModel");
  createButton.addEventListener("click", () => addModel(provider, input.value.trim()));

  const cancelButton = document.createElement("button");
  cancelButton.type = "button";
  cancelButton.className = "btn ghost";
  cancelButton.textContent = t("common.cancel");
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
  if (!state.currentConfig || !state.currentConfig.models || !state.currentConfig.models[modelName]) {
    return;
  }

  const value = normalizeFieldValue(rawValue, options.type);
  setNestedValue(state.currentConfig.models[modelName], path, value);
  if (path === "provider") {
    applyProviderDefaults(state.currentConfig.models[modelName], value);
  }
  syncEditorFromConfig();
  setLocalizedMessage("modelsSummary", "models.summaryDraftUpdated", { model: modelName });
  setLocalizedMessage("editor", "editor.editing", { model: modelName }, { tone: "dirty" });

  if (options.rerender) {
    renderProviderCards(state.currentConfig);
  }
}

function ensureEditableConfig() {
  if (state.currentConfig && state.currentConfig.models) {
    return true;
  }

  try {
    const parsed = parseJsonObject(configJsonInput.value, "field.config");
    if (!parsed.models || typeof parsed.models !== "object") {
      parsed.models = {};
    }
    state.currentConfig = parsed;
    return true;
  } catch (error) {
    setRawMessage("config", formatError(error));
    return false;
  }
}

function addProvider() {
  if (!state.adminUnlocked || !ensureEditableConfig()) return;
  const normalized = providerNameInput.value.trim();
  const providerType = providerTypeInput.value;
  if (!normalized) return;

  const hasProvider = Object.values(state.currentConfig.models).some(
    (model) => getProviderGroupName(model) === normalized
  );
  if (hasProvider) {
    setLocalizedMessage("modelsSummary", "models.summaryProviderExists", { provider: normalized });
    return;
  }

  const modelName = createUniqueModelName(slugify(normalized) || "model");
  state.currentConfig.models[modelName] = buildDefaultModel(normalized, providerType);
  syncEditorFromConfig();
  renderProviderCards(state.currentConfig);
  setLocalizedMessage("modelsSummary", "models.summaryProviderAdded", {
    provider: normalized,
    providerType,
    model: modelName,
  });
  setLocalizedMessage("editor", "editor.addedProvider", { provider: normalized }, { tone: "dirty" });
  hideProviderCreator();
}

function addModel(provider, modelName) {
  if (!state.adminUnlocked || !ensureEditableConfig()) return;
  if (!modelName) return;
  if (state.currentConfig.models[modelName]) {
    setLocalizedMessage("modelsSummary", "models.summaryModelExists", { model: modelName });
    return;
  }

  const providerType = findProviderType(provider);
  state.currentConfig.models[modelName] = buildDefaultModel(provider, providerType);
  syncEditorFromConfig();
  providerState.set(provider, false);
  renderProviderCards(state.currentConfig);
  setLocalizedMessage("modelsSummary", "models.summaryModelAdded", { model: modelName, provider });
  setLocalizedMessage("editor", "editor.addedModel", { model: modelName }, { tone: "dirty" });
}

function deleteModel(modelName) {
  if (!state.adminUnlocked || !ensureEditableConfig() || !state.currentConfig.models[modelName]) return;
  const references = collectModelReferences(modelName);
  if (references.length) {
    setLocalizedMessage("modelsSummary", "models.summaryDeleteModelBlocked", {
      model: modelName,
      refs: references.join(", "),
    });
    return;
  }
  const confirmed = window.confirm(t("confirm.deleteModel", { model: modelName }));
  if (!confirmed) return;

  delete state.currentConfig.models[modelName];
  syncEditorFromConfig();
  renderProviderCards(state.currentConfig);
  setLocalizedMessage("modelsSummary", "models.summaryModelDeleted", { model: modelName });
  setLocalizedMessage("editor", "editor.deletedModel", { model: modelName }, { tone: "dirty" });
}

function deleteProvider(provider) {
  if (!state.adminUnlocked || !ensureEditableConfig()) return;
  const modelNames = Object.entries(state.currentConfig.models)
    .filter(([, model]) => getProviderGroupName(model) === provider)
    .map(([name]) => name);

  if (!modelNames.length) return;

  const referenced = modelNames.flatMap((name) => collectModelReferences(name).map((ref) => `${name}:${ref}`));
  if (referenced.length) {
    setLocalizedMessage("modelsSummary", "models.summaryDeleteProviderBlocked", {
      provider,
      refs: referenced.join(", "),
    });
    return;
  }

  const confirmed = window.confirm(t("confirm.deleteProvider", { provider, count: modelNames.length }));
  if (!confirmed) return;

  modelNames.forEach((name) => {
    delete state.currentConfig.models[name];
  });
  syncEditorFromConfig();
  renderProviderCards(state.currentConfig);
  setLocalizedMessage("modelsSummary", "models.summaryProviderDeleted", { provider });
  setLocalizedMessage("editor", "editor.deletedProvider", { provider }, { tone: "dirty" });
}

function renameModel(oldName, nextName) {
  if (!state.adminUnlocked || !ensureEditableConfig() || !state.currentConfig.models[oldName]) return;
  if (!nextName || nextName === oldName) {
    renderProviderCards(state.currentConfig);
    return;
  }
  if (state.currentConfig.models[nextName]) {
    setLocalizedMessage("modelsSummary", "models.summaryModelExists", { model: nextName });
    renderProviderCards(state.currentConfig);
    return;
  }

  state.currentConfig.models[nextName] = state.currentConfig.models[oldName];
  delete state.currentConfig.models[oldName];
  replaceModelReferences(oldName, nextName);
  syncEditorFromConfig();
  renderProviderCards(state.currentConfig);
  setLocalizedMessage("modelsSummary", "models.summaryModelRenamed", {
    oldName,
    newName: nextName,
  });
  setLocalizedMessage("editor", "editor.renamedModel", { model: oldName }, { tone: "dirty" });
}

function buildDefaultModel(providerGroup, providerType = "openai_compatible") {
  const model = {
    provider: providerType,
    provider_group: providerGroup,
    base_url: "",
    api_key: providerType === "openai_compatible" ? "" : null,
    api_key_header: "Authorization",
    api_key_prefix: "Bearer ",
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
  while (state.currentConfig.models[candidate]) {
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
  if (!state.currentConfig || !state.currentConfig.routing) return [];

  const refs = [];
  const routing = state.currentConfig.routing;
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
  if (!state.currentConfig || !state.currentConfig.routing) return;

  const routing = state.currentConfig.routing;
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
  if (value === null || value === undefined || value === "") return t("common.none");
  return String(value);
}

function applyProviderDefaults(model, providerType) {
  if (!model) return;
  if (providerType === "openai-codex-oauth") {
    model.api_key = null;
    model.api_key_header = "Authorization";
    model.api_key_prefix = "Bearer ";
    model.oauth_token_path = model.oauth_token_path || "~/.codex/auth.json";
    if (!model.base_url) {
      model.base_url = "https://api.openai.com/v1";
    }
    return;
  }

  model.oauth_token_path = null;
  model.api_key = model.api_key || "";
  model.api_key_header = model.api_key_header || "Authorization";
  if (model.api_key_prefix === null || model.api_key_prefix === undefined) {
    model.api_key_prefix = "Bearer ";
  }
}

function translateSource(source) {
  if (source === "file") return t("source.file");
  if (source === "db") return t("source.db");
  if (source === "file-fallback") return t("source.fileFallback");
  return source || t("source.unknown");
}

function buildConfigStatusText(primaryLine, warning) {
  const persistence = state.currentConfigWritable ? t("config.persistenceDb") : t("config.persistenceFile");
  const lines = [
    primaryLine,
    t("config.sourceLine", {
      source: translateSource(state.currentConfigSource),
      persistence,
    }),
  ];
  if (warning) {
    lines.push(t("config.warning", { warning }));
  }
  return lines.join("\n");
}

function syncConfigFromTextareaIfNeeded() {
  try {
    const parsed = parseJsonObject(configJsonInput.value, "field.config");
    state.currentConfig = parsed;
  } catch (_) {
    // Keep currentConfig untouched; validation/save will surface the parse error.
  }
}

function handleConfigTextareaInput() {
  syncConfigFromTextareaIfNeeded();
  state.hasUnsavedChanges = configJsonInput.value !== state.lastLoadedConfigJson;
  updateEditorActions();
  setLocalizedMessage(
    "editor",
    state.hasUnsavedChanges ? "editor.jsonChanged" : "editor.jsonMatches",
    {},
    { tone: state.hasUnsavedChanges ? "dirty" : "ready" }
  );
}

function applyLoadedConfig(config) {
  state.currentConfig = config;
  configJsonInput.value = formatJson(state.currentConfig);
  state.lastLoadedConfigJson = configJsonInput.value;
  state.hasUnsavedChanges = false;
  updateEditorActions();
}

function syncEditorFromConfig() {
  configJsonInput.value = formatJson(state.currentConfig);
  state.hasUnsavedChanges = configJsonInput.value !== state.lastLoadedConfigJson;
  updateEditorActions();
}

function markPersisted() {
  state.lastLoadedConfigJson = formatJson(state.currentConfig);
  configJsonInput.value = state.lastLoadedConfigJson;
  state.hasUnsavedChanges = false;
  updateEditorActions();
}

function updateEditorActions() {
  const editable = state.adminUnlocked && Boolean(state.currentConfig);
  modelsValidateButton.disabled = !editable;
  modelsLoadButton.disabled = !state.adminUnlocked;
  modelsSaveButton.disabled = !editable || !state.hasUnsavedChanges || !state.currentConfigWritable;
  discardDraftButton.disabled = !state.hasUnsavedChanges;
  configLoadButton.disabled = !state.adminUnlocked;
  configValidateButton.disabled = !editable;
  configSaveButton.disabled = !editable || !state.currentConfigWritable;
  providerAddButton.disabled = !state.adminUnlocked;
}

function showProviderCreator() {
  if (!state.adminUnlocked) return;
  providerCreator.classList.remove("hidden");
  providerNameInput.focus();
}

function hideProviderCreator() {
  providerCreator.classList.add("hidden");
  providerNameInput.value = "";
  providerTypeInput.value = "openai_compatible";
}

function toggleModelCreator(section, provider) {
  if (!state.adminUnlocked) return;
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
  const model = Object.values((state.currentConfig && state.currentConfig.models) || {}).find(
    (item) => item && item.provider && getProviderGroupName(item) === providerGroup
  );
  return model && model.provider ? model.provider : "openai_compatible";
}

function getProviderGroupName(model) {
  return model && model.provider_group ? model.provider_group : model && model.provider ? model.provider : "unknown";
}

function discardDraft() {
  if (!state.hasUnsavedChanges || !state.lastLoadedConfigJson) return;
  const confirmed = window.confirm(t("confirm.discardDraft"));
  if (!confirmed) return;
  configJsonInput.value = state.lastLoadedConfigJson;
  syncConfigFromTextareaIfNeeded();
  state.hasUnsavedChanges = false;
  renderProviderCards(state.currentConfig);
  updateEditorActions();
  setLocalizedMessage("editor", "editor.discarded", {}, { tone: "ready" });
}

function guardUnsavedChanges(event) {
  if (!state.hasUnsavedChanges) return undefined;
  event.preventDefault();
  event.returnValue = t("leave.unsaved");
  return event.returnValue;
}
