let currentModel = "deepseek-v4-pro";
let currentModelTag = "思考";
let currentModelIcon = "🧠";

const SELECTED_RESULTS_STORAGE_KEY = "aiModuleSelectedResults";
const HISTORY_RECORD_STORAGE_KEY = "aiModuleHistoryRecord";

const RESULT_TYPE_LABELS = {
  reports: "分析报告",
  models: "模型结果",
};

const resultState = {
  activeTab: "reports",
  selected: new Map(),
  draftSelected: new Map(),
  results: {
    reports: [],
    models: [],
  },
  demoMode: false,
  loadError: false,
};

const modelState = {
  statuses: {},
  requestId: 0,
};

const historyState = {
  records: [],
  loadError: false,
};

const conversationState = {
  id: null,
  messages: [],
};

const elements = {
  appShell: document.getElementById("appShell"),
  resultModal: document.getElementById("resultModal"),
  historyModal: document.getElementById("historyModal"),
  clearConfirmModal: document.getElementById("clearConfirmModal"),
  modelPicker: document.getElementById("modelPicker"),
  modelSelectButton: document.getElementById("modelSelectButton"),
  modelMenu: document.getElementById("modelMenu"),
  currentModelName: document.getElementById("currentModelName"),
  currentModelTag: document.getElementById("currentModelTag"),
  modelKindIcon: document.getElementById("modelKindIcon"),
  openSelectorButton: document.getElementById("openSelectorButton"),
  openHistoryButton: document.getElementById("openHistoryButton"),
  refreshResultsButton: document.getElementById("refreshResultsButton"),
  closeModalButton: document.getElementById("closeModalButton"),
  confirmSelectionButton: document.getElementById("confirmSelectionButton"),
  closeHistoryButton: document.getElementById("closeHistoryButton"),
  refreshHistoryButton: document.getElementById("refreshHistoryButton"),
  clearChatButton: document.getElementById("clearChatButton"),
  cancelClearButton: document.getElementById("cancelClearButton"),
  keepChatButton: document.getElementById("keepChatButton"),
  confirmClearButton: document.getElementById("confirmClearButton"),
  selectedList: document.getElementById("selectedList"),
  modalResultList: document.getElementById("modalResultList"),
  historyList: document.getElementById("historyList"),
  selectorStatus: document.getElementById("selectorStatus"),
  historyStatus: document.getElementById("historyStatus"),
  tabs: Array.from(document.querySelectorAll(".tabs button")),
  chatForm: document.getElementById("chatForm"),
  questionInput: document.getElementById("questionInput"),
  messages: document.getElementById("messages"),
  quickActions: Array.from(document.querySelectorAll(".quick-actions button")),
  toast: document.getElementById("toast"),
};

let toastTimer = null;
let isGenerating = false;

document.addEventListener("DOMContentLoaded", initializeApp);

async function initializeApp() {
  const pendingHistory = hydratePendingHistoryRecord();
  hydrateSelectedResults();
  bindEvents();
  await loadResults();
  updateModelMenuState();
  if (pendingHistory) {
    applyHistoryRecord(pendingHistory);
  } else {
    renderSelectedSummary();
    resetMessagesToInitial();
  }
  checkModelConnection(currentModel);
}

function bindEvents() {
  elements.openSelectorButton.addEventListener("click", () => openResultModal());
  elements.openHistoryButton.addEventListener("click", openHistoryModal);
  elements.refreshResultsButton.addEventListener("click", refreshResults);
  elements.closeModalButton.addEventListener("click", () => closeModal(elements.resultModal));
  elements.confirmSelectionButton.addEventListener("click", confirmSelection);
  elements.closeHistoryButton.addEventListener("click", () => closeModal(elements.historyModal));
  elements.refreshHistoryButton.addEventListener("click", () => loadHistoryList(true));
  elements.clearChatButton.addEventListener("click", () => openModal(elements.clearConfirmModal));
  elements.cancelClearButton.addEventListener("click", () => closeModal(elements.clearConfirmModal));
  elements.keepChatButton.addEventListener("click", () => closeModal(elements.clearConfirmModal));
  elements.confirmClearButton.addEventListener("click", clearChat);
  elements.modelSelectButton.addEventListener("click", toggleModelMenu);

  elements.modelMenu.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => {
      setCurrentModel(button.dataset.model, button.dataset.tag, button.dataset.icon);
    });
  });

  document.addEventListener("click", (event) => {
    if (!elements.modelPicker.contains(event.target)) {
      closeModelMenu();
    }
  });

  [elements.resultModal, elements.historyModal, elements.clearConfirmModal].forEach((modal) => {
    modal.addEventListener("click", (event) => {
      if (event.target === modal) {
        closeModal(modal);
      }
    });
  });

  elements.tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      resultState.activeTab = tab.dataset.tab;
      renderTabs();
      renderResultLists();
    });
  });

  elements.quickActions.forEach((button) => {
    button.addEventListener("click", () => {
      askQuestion(button.dataset.question);
    });
  });

  elements.messages.addEventListener("click", (event) => {
    const button = event.target.closest("[data-empty-question]");
    if (button) {
      askQuestion(button.dataset.emptyQuestion);
    }
  });

  elements.historyList.addEventListener("click", (event) => {
    const historyButton = event.target.closest("[data-history-id]");
    if (historyButton) {
      loadHistoryRecord(historyButton.dataset.historyId);
    }
  });

  elements.chatForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const question = elements.questionInput.value.trim();
    askQuestion(question);
  });

  elements.questionInput.addEventListener("input", autoResizeTextarea);
  elements.questionInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      elements.chatForm.requestSubmit();
    }
  });
}

async function loadResults() {
  try {
    const response = await fetch("/api/results");
    if (!response.ok) {
      throw new Error("results api unavailable");
    }

    const data = await response.json();
    resultState.results = normalizeResults(data);
    reconcileSelectedResults();
    resultState.demoMode = false;
    resultState.loadError = false;
  } catch (error) {
    resultState.results = { reports: [], models: [] };
    resultState.selected.clear();
    persistSelectedResults();
    resultState.demoMode = false;
    resultState.loadError = true;
    setSelectorStatus("读取 result 目录失败，请确认后端 /api/results 已启动。");
  }

  renderTabs();
  renderResultLists();
  renderSelectedSummary();
}

function normalizeResults(data) {
  const source = data.results || data;
  return {
    reports: normalizeResultFiles(source.reports, "reports"),
    models: normalizeResultFiles(source.models, "models"),
  };
}

function normalizeResultFiles(files, type) {
  if (!Array.isArray(files)) {
    return [];
  }

  return files.map((file) => ({
    ...file,
    name: file.name || file.file_name || file.path || file.file_path || "未命名结果",
    path: file.path || file.file_path || file.name || file.file_name || "",
    type: file.type || file.file_type || file.category || type,
    category: file.category || file.type || file.file_type || type,
    created_at: file.created_at || file.file_created_at || file.createdAt || file.created || file.mtime || file.modified_at || "",
  }));
}

function reconcileSelectedResults() {
  const nextSelected = new Map();

  for (const [key, file] of resultState.selected.entries()) {
    const currentFile = findFileByKey(key);
    if (currentFile) {
      nextSelected.set(key, {
        ...currentFile,
        supplemented: Boolean(file.supplemented),
      });
    }
  }

  resultState.selected = nextSelected;
  persistSelectedResults();
}

function setSelectorStatus(text) {
  elements.selectorStatus.textContent = text;
}

function renderTabs() {
  elements.tabs.forEach((tab) => {
    tab.classList.toggle("active", tab.dataset.tab === resultState.activeTab);
  });
}

function renderResultLists() {
  renderResultList(elements.modalResultList);
  updateSelectorHint();
}

function renderResultList(container) {
  const files = resultState.results[resultState.activeTab] || [];

  if (files.length === 0) {
    container.innerHTML = `<div class="empty-state">${getEmptyStateText()}</div>`;
    return;
  }

  container.innerHTML = files
    .map((file) => {
      const fileKey = getFileKey(resultState.activeTab, file);
      const checked = resultState.draftSelected.has(fileKey) ? "checked" : "";
      const alreadySelected = resultState.selected.has(fileKey);
      const name = escapeHtml(file.name || file.path || "未命名结果");
      const path = escapeHtml(file.path || file.name || "");
      const createdAt = escapeHtml(formatDate(file.created_at));
      const disabled = alreadySelected ? "disabled" : "";
      const itemClass = alreadySelected ? "result-item locked" : "result-item";
      const selectedHint = alreadySelected ? `<span class="selected-badge">已在当前对话中</span>` : "";

      return `
        <div class="${itemClass}">
          <label>
            <input type="checkbox" data-key="${escapeHtml(fileKey)}" ${checked} ${disabled}>
            <span class="file-content">
              <span class="file-name">${name}${selectedHint}</span>
              <span class="file-meta">
                <span class="meta-row">
                  ${calendarIcon()}
                  <span>${createdAt}</span>
                </span>
                <span class="meta-row">
                  ${pathIcon()}
                  <span>${path}</span>
                </span>
              </span>
            </span>
          </label>
        </div>
      `;
    })
    .join("");

  container.querySelectorAll("input[type='checkbox']").forEach((checkbox) => {
    checkbox.addEventListener("change", () => toggleSelection(checkbox));
  });
}

function getEmptyStateText() {
  if (resultState.activeTab === "models") {
    return "当前分类暂无可补充 CSV 模型结果。";
  }

  return "当前分类暂无可补充结果。";
}

function updateSelectorHint() {
  if (resultState.loadError) {
    return;
  }


  setSelectorStatus("");
}

function toggleSelection(checkbox) {
  if (checkbox.disabled) {
    return;
  }

  const file = findFileByKey(checkbox.dataset.key);
  if (!file) {
    return;
  }

  if (checkbox.checked) {
    resultState.draftSelected.set(checkbox.dataset.key, file);
  } else {
    resultState.draftSelected.delete(checkbox.dataset.key);
  }

  renderResultLists();
}

function findFileByKey(key) {
  for (const [type, files] of Object.entries(resultState.results)) {
    const match = files.find((file) => getFileKey(type, file) === key);
    if (match) {
      return {
        type: match.type || match.category || type,
        category: match.category || match.type || type,
        name: match.name || match.path || "未命名结果",
        path: match.path || match.name || "",
        created_at: match.created_at || "",
      };
    }
  }

  return null;
}

function getFileKey(type, file) {
  return `${type}:${file.path || file.name}`;
}

function formatDate(value) {
  if (!value) {
    return "创建日期待同步";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  const seconds = String(date.getSeconds()).padStart(2, "0");
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
}

function confirmSelection() {
  const addedFiles = getAddedDraftFiles();

  if (addedFiles.length === 0) {
    showToast("请选择要补充的文件", "warning");
    return;
  }

  const addedFileKeys = new Set(addedFiles.map((file) => getFileKey(file.type, file)));
  const nextSelected = new Map();

  for (const [key, file] of resultState.draftSelected.entries()) {
    const currentFile = resultState.selected.get(key);
    nextSelected.set(key, {
      ...file,
      supplemented: Boolean(currentFile?.supplemented || addedFileKeys.has(key)),
    });
  }

  resultState.selected = nextSelected;
  renderSelectedSummary();
  persistSelectedResults();
  closeModal(elements.resultModal);
  addSupplementMessage(addedFiles);
  showToast("已补充待分析文件");
}

function getAddedDraftFiles() {
  const addedFiles = [];

  for (const [key, file] of resultState.draftSelected.entries()) {
    if (!resultState.selected.has(key)) {
      addedFiles.push(file);
    }
  }

  return addedFiles;
}

function hydrateSelectedResults() {
  try {
    const selectedResults = JSON.parse(sessionStorage.getItem(SELECTED_RESULTS_STORAGE_KEY) || "[]");
    if (!Array.isArray(selectedResults)) {
      return;
    }

    selectedResults.forEach((file) => {
      if (!file || !file.type) {
        return;
      }

      resultState.selected.set(getFileKey(file.type, file), {
        type: file.type,
        name: file.name || file.path || "未命名结果",
        path: file.path || file.name || "",
        created_at: file.created_at || "",
        supplemented: Boolean(file.supplemented),
      });
    });
  } catch (error) {
    resultState.selected.clear();
  }
}

function persistSelectedResults() {
  sessionStorage.setItem(SELECTED_RESULTS_STORAGE_KEY, JSON.stringify(Array.from(resultState.selected.values())));
}

function renderSelectedSummary() {
  const selected = Array.from(resultState.selected.values());

  if (selected.length === 0) {
    elements.selectedList.textContent = "已选择 0 个结果";
    return;
  }

  const preview = selected
    .slice(0, 2)
    .map((file) => `${RESULT_TYPE_LABELS[file.type] || file.type}：${file.name}`)
    .join("；");
  const rest = selected.length > 2 ? ` 等 ${selected.length} 个结果` : "";
  elements.selectedList.textContent = `已选择 ${selected.length} 个结果 · ${preview}${rest}`;
}

function getConversationHistoryForApi() {
  return conversationState.messages
    .filter((message) => ["user", "assistant"].includes(message.role))
    .map((message) => ({
      role: message.role,
      content: message.content,
      reasoning: message.reasoning || "",
      created_at: message.created_at || "",
      model: message.model || "",
      is_error: Boolean(message.is_error),
    }));
}

async function saveCurrentHistory() {
  const hasUserMessage = conversationState.messages.some((message) => message.role === "user");
  if (!hasUserMessage) {
    return;
  }

  try {
    const response = await fetch("/api/history/save", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        id: conversationState.id,
        model: currentModel,
        selected_results: Array.from(resultState.selected.values()),
        messages: conversationState.messages,
      }),
    });

    if (!response.ok) {
      throw new Error("history save unavailable");
    }

    const data = await response.json();
    conversationState.id = data.id || data.history?.id || conversationState.id;
  } catch (error) {
    showToast("历史记录保存失败", "warning");
  }
}

function hydratePendingHistoryRecord() {
  try {
    const rawHistory = sessionStorage.getItem(HISTORY_RECORD_STORAGE_KEY);
    if (!rawHistory) {
      return null;
    }

    sessionStorage.removeItem(HISTORY_RECORD_STORAGE_KEY);
    return JSON.parse(rawHistory);
  } catch (error) {
    sessionStorage.removeItem(HISTORY_RECORD_STORAGE_KEY);
    return null;
  }
}

function applyHistoryRecord(record) {
  const history = normalizeHistoryRecord(record);
  conversationState.id = history.id;
  conversationState.messages = history.messages;
  resultState.selected = new Map();

  history.selected_results.forEach((file) => {
    resultState.selected.set(getFileKey(file.type, file), file);
  });

  persistSelectedResults();
  renderSelectedSummary();
  renderConversationMessages();
  showToast("已载入历史对话");
}

function normalizeHistoryRecord(record) {
  const source = record?.history || record || {};
  return {
    id: source.id || "",
    selected_results: normalizeSelectedResults(source.selected_results || source.selected_files || []),
    messages: normalizeConversationMessages(source.messages || []),
  };
}

function normalizeSelectedResults(files) {
  if (!Array.isArray(files)) {
    return [];
  }

  return files.map((file) => ({
    type: file.type || file.category || file.file_type || "unknown",
    category: file.category || file.type || file.file_type || "unknown",
    name: file.name || file.file_name || file.path || file.file_path || "未命名结果",
    path: file.path || file.file_path || file.name || file.file_name || "",
    created_at: file.created_at || file.file_created_at || "",
    supplemented: Boolean(file.supplemented),
  }));
}

function normalizeConversationMessages(messages) {
  if (!Array.isArray(messages)) {
    return [];
  }

  return messages
    .filter((message) => message && ["user", "assistant"].includes(message.role) && message.content)
    .map((message) => ({
      role: message.role,
      content: String(message.content),
      reasoning: String(message.reasoning || ""),
      created_at: message.created_at || "",
      model: message.model || "",
      is_error: Boolean(message.is_error),
    }));
}

function renderConversationMessages() {
  if (conversationState.messages.length === 0) {
    resetMessagesToInitial();
    return;
  }

  elements.messages.classList.remove("empty");
  elements.messages.innerHTML = "";

  conversationState.messages.forEach((message) => {
    if (message.role === "user") {
      addUserMessage(message.content, message.created_at || "时间待同步");
    }

    if (message.role === "assistant") {
      addAssistantMessage(message);
    }
  });
}

async function askQuestion(question) {
  if (isGenerating) {
    showToast("请等待模型回答完成", "warning");
    return;
  }

  const trimmedQuestion = question.trim();
  if (!trimmedQuestion) {
    showToast("请输入问题后再发送", "warning");
    return;
  }

  const selectedResults = Array.from(resultState.selected.values());
  const historyBeforeQuestion = getConversationHistoryForApi();
  const questionTime = formatMessageTime(new Date());
  const userMessage = {
    role: "user",
    content: trimmedQuestion,
    created_at: questionTime,
  };

  ensureChatStarted();
  addUserMessage(trimmedQuestion, questionTime);
  conversationState.messages.push(userMessage);
  elements.questionInput.value = "";
  autoResizeTextarea();

  const loadingId = addLoadingMessage();
  setGeneratingState(true);

  try {
    const answer = await requestAiAnswer(trimmedQuestion, selectedResults, historyBeforeQuestion, (streamingAnswer) => {
      replaceLoadingMessage(loadingId, {
        reasoning: streamingAnswer.reasoning || "正在生成思考结果...",
        content: streamingAnswer.content || "正在生成回答结果...",
        isFinal: false,
      });
    });
    const completedAt = formatMessageTime(new Date());
    replaceLoadingMessage(loadingId, {
      ...answer,
      completedAt,
      isFinal: true,
    });
    conversationState.messages.push({
      role: "assistant",
      content: answer.content,
      reasoning: answer.reasoning,
      created_at: completedAt,
      model: currentModel,
    });
    await saveCurrentHistory();
  } catch (error) {
    const completedAt = formatMessageTime(new Date());
    const errorContent = error.message || "请检查 Flask 服务是否已启动，以及 DeepSeek API 配置是否可用。";
    replaceLoadingMessage(loadingId, {
      reasoning: "后端问答接口调用失败。",
      content: errorContent,
      completedAt,
      isFinal: true,
      keepReasoningOpen: true,
    });
    conversationState.messages.push({
      role: "assistant",
      content: errorContent,
      reasoning: "后端问答接口调用失败。",
      created_at: completedAt,
      model: currentModel,
      is_error: true,
    });
    await saveCurrentHistory();
  } finally {
    setGeneratingState(false);
  }
}

async function requestAiAnswer(question, selectedResults, conversationHistory, onDelta) {
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: currentModel,
      question,
      selected_results: selectedResults,
      conversation_history: conversationHistory,
    }),
  });

  if (!response.ok) {
    throw new Error("chat api unavailable");
  }

  const contentType = response.headers.get("content-type") || "";
  if (response.body && contentType.includes("text/event-stream")) {
    return readChatStream(response.body, onDelta);
  }

  const data = await response.json();
  return {
    reasoning: data.reasoning || data.reasoning_content || "未返回思考结果。",
    content: data.content || data.answer || "未返回回答结果。",
  };
}

async function readChatStream(body, onDelta) {
  const reader = body.getReader();
  const decoder = new TextDecoder("utf-8");
  const answer = {
    reasoning: "",
    content: "",
  };
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split("\n\n");
    buffer = events.pop() || "";

    for (const event of events) {
      handleChatStreamEvent(event, answer, onDelta);
    }
  }

  if (buffer.trim()) {
    handleChatStreamEvent(buffer, answer, onDelta);
  }

  return {
    reasoning: answer.reasoning || "未返回思考结果。",
    content: answer.content || "未返回回答结果。",
  };
}

function handleChatStreamEvent(event, answer, onDelta) {
  const dataText = event
    .split("\n")
    .filter((line) => line.startsWith("data:"))
    .map((line) => line.replace(/^data:\s?/, ""))
    .join("\n")
    .trim();

  if (!dataText) {
    return;
  }

  const data = JSON.parse(dataText);

  if (data.type === "error") {
    throw new Error(data.message || "chat stream error");
  }

  if (data.type === "reasoning") {
    answer.reasoning += data.delta || "";
  }

  if (data.type === "content") {
    answer.content += data.delta || "";
  }

  if (typeof onDelta === "function" && (data.type === "reasoning" || data.type === "content")) {
    onDelta({ ...answer });
  }
}

function resetMessagesToInitial() {
  elements.messages.classList.add("empty");
  elements.messages.innerHTML = `
    <section class="empty-chat" aria-label="聊天欢迎内容">
      <div class="empty-chat-icon" aria-hidden="true">
        <svg viewBox="0 0 24 24">
          <path d="M4 5h16v10H8.4L4 19.4V5Zm2 2v7.6L7.6 13H18V7H6Zm3 2h6v2H9V9Z"></path>
        </svg>
      </div>
      <h2>欢迎使用电商数据智能分析助手！</h2>
      <p>已载入所选分析结果。你可以直接点击推荐问题，也可以在底部输入框中手动提问。</p>
      <div class="empty-recommendations" aria-label="推荐问题">
        <h3>推荐问题</h3>
        <div class="empty-recommendation-list">
          <button type="button" data-empty-question="请结合当前所选分析报告和模型结果，总结最值得关注的业务结论。">
            <span>总结当前结果中最重要的业务结论</span>
            <span class="arrow" aria-hidden="true">→</span>
          </button>
          <button type="button" data-empty-question="请分析当前用户分群结果，并给出不同用户群体的运营策略。">
            <span>分析用户分群，并给出运营策略</span>
            <span class="arrow" aria-hidden="true">→</span>
          </button>
          <button type="button" data-empty-question="请根据所选分析报告，找出影响转化的关键问题。">
            <span>找出影响转化的关键问题</span>
            <span class="arrow" aria-hidden="true">→</span>
          </button>
          <button type="button" data-empty-question="请基于关联规则结果，推荐适合捆绑销售和交叉推荐的商品组合。">
            <span>推荐捆绑销售和交叉推荐组合</span>
            <span class="arrow" aria-hidden="true">→</span>
          </button>
        </div>
      </div>
    </section>
  `;
}

function ensureChatStarted() {
  if (!elements.messages.classList.contains("empty")) {
    return;
  }

  elements.messages.classList.remove("empty");
  elements.messages.innerHTML = "";
}

function addUserMessage(text, sentAt) {
  const article = document.createElement("article");
  article.className = "message user-message";
  article.innerHTML = `
    <div class="avatar">我</div>
    <div class="message-body">
      <div class="message-meta"><strong>用户</strong></div>
      <p>${escapeHtml(text)}</p>
      <div class="message-time">${escapeHtml(sentAt)}</div>
    </div>
  `;
  elements.messages.appendChild(article);
  scrollToBottom();
}

function addSupplementMessage(files) {
  ensureChatStarted();
  const article = document.createElement("article");
  article.className = "message ai-message system-message";
  const fileList = files
    .map((file) => `- ${RESULT_TYPE_LABELS[file.type] || file.type}：${file.name}`)
    .join("\n");

  article.innerHTML = `
    <div class="avatar">AI</div>
    <div class="message-body">
      <div class="message-meta"><strong>系统提示</strong></div>
      <div class="markdown-content">${renderMarkdown(`已补充以下待分析文件，后续提问会一并提供给 DeepSeek：\n${fileList}`)}</div>
      <div class="message-time">${escapeHtml(formatMessageTime(new Date()))}</div>
    </div>
  `;
  elements.messages.appendChild(article);
  scrollToBottom();
}

function addLoadingMessage() {
  const id = `loading-${Date.now()}`;
  const article = document.createElement("article");
  article.className = "message ai-message";
  article.id = id;
  article.innerHTML = `
    <div class="avatar">AI</div>
    <div class="message-body">
      <div class="message-meta"><strong>DeepSeek</strong><span>${currentModel}</span></div>
      <p>正在生成思考结果和回答结果...</p>
    </div>
  `;
  elements.messages.appendChild(article);
  scrollToBottom();
  return id;
}

function replaceLoadingMessage(id, answer) {
  const article = document.getElementById(id);
  if (!article) {
    return;
  }

  const reasoningOpen = answer.keepReasoningOpen || !answer.isFinal ? "open" : "";
  const completedAt = answer.completedAt ? `<div class="message-time">${escapeHtml(answer.completedAt)}</div>` : "";

  article.innerHTML = `
    <div class="avatar">AI</div>
    <div class="message-body">
      <div class="message-meta"><strong>DeepSeek</strong><span>${currentModel}</span></div>
      <details class="reasoning-block" ${reasoningOpen}>
        <summary>
          <span class="box-title">思考</span>
          <span class="reasoning-toggle">展开/收起</span>
        </summary>
        <div class="markdown-content">${renderMarkdown(answer.reasoning)}</div>
      </details>
      <div class="answer-block">
        <div class="markdown-content">${renderMarkdown(answer.content)}</div>
      </div>
      ${completedAt}
    </div>
  `;
  scrollToBottom();
}

function addAssistantMessage(message) {
  const article = document.createElement("article");
  article.className = "message ai-message";
  const model = message.model || currentModel;
  const completedAt = message.created_at ? `<div class="message-time">${escapeHtml(message.created_at)}</div>` : "";
  const reasoningBlock = message.reasoning
    ? `
      <details class="reasoning-block">
        <summary>
          <span class="box-title">思考</span>
          <span class="reasoning-toggle">展开/收起</span>
        </summary>
        <div class="markdown-content">${renderMarkdown(message.reasoning)}</div>
      </details>
    `
    : "";

  article.innerHTML = `
    <div class="avatar">AI</div>
    <div class="message-body">
      <div class="message-meta"><strong>DeepSeek</strong><span>${escapeHtml(model)}</span></div>
      ${reasoningBlock}
      <div class="answer-block">
        <div class="markdown-content">${renderMarkdown(message.content)}</div>
      </div>
      ${completedAt}
    </div>
  `;
  elements.messages.appendChild(article);
  scrollToBottom();
}

function clearChat() {
  conversationState.id = null;
  conversationState.messages = [];
  resetMessagesToInitial();
  closeModal(elements.clearConfirmModal);
  showToast("对话已清空");
}

function openModal(modal) {
  modal.classList.remove("hidden", "closing");
}

async function openHistoryModal() {
  if (isGenerating) {
    showToast("请等待模型回答完成", "warning");
    return;
  }

  await loadHistoryList();
  openModal(elements.historyModal);
}

function openResultModal() {
  resultState.draftSelected = new Map(resultState.selected);
  renderResultLists();
  openModal(elements.resultModal);
}

async function loadHistoryList(showSuccessToast = false) {
  try {
    const response = await fetch("/api/history");
    if (!response.ok) {
      throw new Error("history api unavailable");
    }

    const data = await response.json();
    historyState.records = Array.isArray(data.history) ? data.history : [];
    historyState.loadError = false;
    setHistoryStatus("");
    renderHistoryList();
    if (showSuccessToast) {
      showToast("历史记录已刷新");
    }
  } catch (error) {
    historyState.records = [];
    historyState.loadError = true;
    setHistoryStatus("读取历史记录失败，请确认后端 /api/history 已启动。");
    renderHistoryList();
  }
}

function renderHistoryList() {
  if (historyState.loadError) {
    elements.historyList.innerHTML = `<div class="empty-state">历史记录读取失败。</div>`;
    return;
  }

  if (historyState.records.length === 0) {
    elements.historyList.innerHTML = `<div class="empty-state">当前暂无历史对话。</div>`;
    return;
  }

  elements.historyList.innerHTML = historyState.records
    .map((record) => {
      const isCurrent = conversationState.id && record.id === conversationState.id;
      const selectedFiles = formatHistoryFiles(record.selected_files || record.selected_results || []);
      const currentBadge = isCurrent ? `<span class="selected-badge">当前对话</span>` : "";
      return `
        <button class="history-item ${isCurrent ? "current" : ""}" type="button" data-history-id="${escapeHtml(record.id)}">
          <span class="history-title">${escapeHtml(record.first_question || "未命名历史对话")}${currentBadge}</span>
          <span class="history-meta">
            <span>${calendarIcon()}${escapeHtml(record.created_at || "时间待同步")}</span>
            <span>${pathIcon()}${escapeHtml(selectedFiles || "未记录分析文件")}</span>
          </span>
        </button>
      `;
    })
    .join("");
}

async function loadHistoryRecord(historyId) {
  if (!historyId) {
    return;
  }

  if (isGenerating) {
    showToast("请等待模型回答完成", "warning");
    return;
  }

  try {
    const response = await fetch(`/api/history/${encodeURIComponent(historyId)}`);
    if (!response.ok) {
      throw new Error("history detail unavailable");
    }

    const data = await response.json();
    applyHistoryRecord(data.history || data);
    closeModal(elements.historyModal);
  } catch (error) {
    showToast("历史对话读取失败", "warning");
  }
}

function formatHistoryFiles(files) {
  if (!Array.isArray(files) || files.length === 0) {
    return "";
  }

  const preview = files
    .slice(0, 2)
    .map((file) => `${RESULT_TYPE_LABELS[file.type] || file.type || "结果"}：${file.name || file.path || "未命名结果"}`)
    .join("；");
  const rest = files.length > 2 ? ` 等 ${files.length} 个文件` : "";
  return `${preview}${rest}`;
}

function setHistoryStatus(text) {
  elements.historyStatus.textContent = text;
}

async function refreshResults() {
  await loadResults();
  resultState.draftSelected = new Map(resultState.selected);
  renderResultLists();
  showToast("文件列表已刷新");
}

function closeModal(modal) {
  if (modal.classList.contains("hidden") || modal.classList.contains("closing")) {
    return;
  }

  if (modal === elements.resultModal && resultState.selected.size === 0) {
    showToast("请至少保留一个待分析结果", "warning");
    return;
  }

  modal.classList.add("closing");
  window.setTimeout(() => {
    modal.classList.add("hidden");
    modal.classList.remove("closing");
  }, 170);
}

function showToast(message, type = "success") {
  window.clearTimeout(toastTimer);
  const icon = type === "warning" ? "!" : "✓";
  elements.toast.className = `toast ${type}`;
  elements.toast.innerHTML = `<span class="toast-icon" aria-hidden="true">${icon}</span><span>${escapeHtml(message)}</span>`;
  requestAnimationFrame(() => {
    elements.toast.classList.add("show");
  });
  toastTimer = window.setTimeout(() => {
    elements.toast.classList.remove("show");
  }, 1800);
}

function toggleModelMenu() {
  const willOpen = elements.modelMenu.classList.contains("hidden");
  elements.modelMenu.classList.toggle("hidden", !willOpen);
  elements.modelSelectButton.setAttribute("aria-expanded", String(willOpen));
}

function closeModelMenu() {
  elements.modelMenu.classList.add("hidden");
  elements.modelSelectButton.setAttribute("aria-expanded", "false");
}

function setCurrentModel(model, tag, icon) {
  currentModel = model;
  currentModelTag = tag;
  currentModelIcon = icon;
  elements.currentModelName.textContent = currentModel;
  elements.currentModelTag.textContent = currentModelTag;
  elements.modelKindIcon.textContent = currentModelIcon;
  updateModelMenuState();
  closeModelMenu();
  showToast(`已切换为 ${currentModelTag} 模型`);
  checkModelConnection(currentModel);
}

function updateModelMenuState() {
  elements.modelMenu.querySelectorAll("button").forEach((button) => {
    const isActive = button.dataset.model === currentModel;
    button.classList.toggle("active", isActive);
    button.setAttribute("aria-current", isActive ? "true" : "false");
    updateModelButtonStatus(button);
  });

  updateCurrentModelStatus();
}

function updateModelButtonStatus(button) {
  const status = modelState.statuses[button.dataset.model] || "idle";
  const statusText = button.querySelector(".model-status");
  const dot = button.querySelector(".status-dot");

  if (!statusText || !dot) {
    return;
  }

  dot.classList.remove("connecting", "success", "error");
  dot.classList.add(getModelStatusClass(status));
  statusText.classList.remove("connecting", "success", "error");
  statusText.classList.add(getModelStatusClass(status));
  setModelStatusLabel(statusText, getModelStatusText(status));
}

function updateCurrentModelStatus() {
  const status = modelState.statuses[currentModel] || "idle";
  const dot = elements.modelSelectButton.querySelector(".compact-status-dot");

  if (!dot) {
    return;
  }

  dot.classList.remove("connecting", "success", "error");
  dot.classList.add(getModelStatusClass(status));
  dot.setAttribute("aria-label", getModelStatusText(status));
  elements.modelSelectButton.title = getModelStatusText(status);
}

function getModelStatusClass(status) {
  if (status === "checking") {
    return "connecting";
  }

  if (status === "success") {
    return "success";
  }

  if (status === "error") {
    return "error";
  }

  return "connecting";
}

function getModelStatusText(status) {
  if (status === "checking") {
    return "连接中";
  }

  if (status === "success") {
    return "连接成功";
  }

  if (status === "error") {
    return "连接失败";
  }

  return "连接中";
}

function setModelStatusLabel(container, text) {
  const labelNode = Array.from(container.childNodes).find((node) => node.nodeType === 3);

  if (labelNode) {
    labelNode.textContent = text;
    return;
  }

  container.append(text);
}

async function checkModelConnection(model) {
  const requestId = ++modelState.requestId;
  modelState.statuses[model] = "checking";
  updateModelMenuState();

  try {
    const response = await fetch("/api/model-status", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ model }),
    });
    const data = await response.json();

    if (requestId < modelState.requestId && model !== currentModel) {
      return;
    }

    modelState.statuses[model] = response.ok && data.status === "success" ? "success" : "error";
  } catch (error) {
    modelState.statuses[model] = "error";
  }

  updateModelMenuState();
}

function setGeneratingState(generating) {
  isGenerating = generating;
  elements.questionInput.readOnly = generating;
  elements.chatForm.querySelector("button[type='submit']").setAttribute("aria-disabled", String(generating));
  elements.quickActions.forEach((button) => {
    button.setAttribute("aria-disabled", String(generating));
  });
}

function autoResizeTextarea() {
  elements.questionInput.style.height = "auto";
  elements.questionInput.style.height = `${Math.min(elements.questionInput.scrollHeight, 140)}px`;
}

function scrollToBottom() {
  elements.messages.scrollTop = elements.messages.scrollHeight;
}

function formatMessageTime(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  const seconds = String(date.getSeconds()).padStart(2, "0");
  return `${year}.${month}.${day} ${hours}:${minutes}:${seconds}`;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderMarkdown(markdown) {
  const codeBlocks = [];
  const source = String(markdown || "").replace(/\r\n/g, "\n");
  const withoutCodeBlocks = source.replace(/```[^\n]*\n?([\s\S]*?)```/g, (match, code) => {
    const token = `@@CODE_BLOCK_${codeBlocks.length}@@`;
    codeBlocks.push(`<pre><code>${escapeHtml(code.trim())}</code></pre>`);
    return `\n${token}\n`;
  });

  const html = renderMarkdownLines(withoutCodeBlocks);

  return codeBlocks.reduce((result, codeBlock, index) => {
    return result.replace(`@@CODE_BLOCK_${index}@@`, codeBlock);
  }, html);
}

function renderMarkdownLines(source) {
  const lines = source.split("\n");
  const html = [];
  let index = 0;

  while (index < lines.length) {
    const line = lines[index].trim();

    if (!line) {
      index += 1;
      continue;
    }

    if (/^@@CODE_BLOCK_\d+@@$/.test(line)) {
      html.push(line);
      index += 1;
      continue;
    }

    if (/^---+$/.test(line)) {
      html.push("<hr>");
      index += 1;
      continue;
    }

    if (isMarkdownTableStart(lines, index)) {
      const tableResult = renderMarkdownTable(lines, index);
      html.push(tableResult.html);
      index = tableResult.nextIndex;
      continue;
    }

    const headingMatch = line.match(/^(#{1,6})\s+(.+)$/);
    if (headingMatch) {
      const level = Math.min(headingMatch[1].length, 3);
      html.push(`<h${level}>${renderInlineMarkdown(headingMatch[2])}</h${level}>`);
      index += 1;
      continue;
    }

    if (/^\s*[-*]\s+/.test(lines[index])) {
      const items = [];
      while (index < lines.length && /^\s*[-*]\s+/.test(lines[index])) {
        items.push(`<li>${renderInlineMarkdown(lines[index].replace(/^\s*[-*]\s+/, ""))}</li>`);
        index += 1;
      }
      html.push(`<ul>${items.join("")}</ul>`);
      continue;
    }

    if (/^\s*\d+\.\s+/.test(lines[index])) {
      const items = [];
      while (index < lines.length && /^\s*\d+\.\s+/.test(lines[index])) {
        items.push(`<li>${renderInlineMarkdown(lines[index].replace(/^\s*\d+\.\s+/, ""))}</li>`);
        index += 1;
      }
      html.push(`<ol>${items.join("")}</ol>`);
      continue;
    }

    const paragraphLines = [];
    while (
      index < lines.length &&
      lines[index].trim() &&
      !/^@@CODE_BLOCK_\d+@@$/.test(lines[index].trim()) &&
      !isMarkdownTableStart(lines, index) &&
      !/^(#{1,6})\s+/.test(lines[index].trim()) &&
      !/^---+$/.test(lines[index].trim()) &&
      !/^\s*[-*]\s+/.test(lines[index]) &&
      !/^\s*\d+\.\s+/.test(lines[index])
    ) {
      paragraphLines.push(lines[index].trim());
      index += 1;
    }

    html.push(`<p>${paragraphLines.map(renderInlineMarkdown).join("<br>")}</p>`);
  }

  return html.join("");
}

function isMarkdownTableStart(lines, index) {
  if (index + 1 >= lines.length) {
    return false;
  }

  const headerCells = splitMarkdownTableRow(lines[index]);
  const separatorCells = splitMarkdownTableRow(lines[index + 1]);
  return (
    headerCells.length > 1 &&
    headerCells.length === separatorCells.length &&
    separatorCells.every(isMarkdownTableSeparatorCell)
  );
}

function splitMarkdownTableRow(line) {
  const trimmed = line.trim();
  if (!trimmed.includes("|") || /^@@CODE_BLOCK_\d+@@$/.test(trimmed)) {
    return [];
  }

  const normalized = trimmed.replace(/^\|/, "").replace(/\|$/, "");
  return normalized.split("|").map((cell) => cell.trim());
}

function isMarkdownTableSeparatorCell(cell) {
  return /^:?-{3,}:?$/.test(cell.trim());
}

function getMarkdownTableAlign(separatorCell) {
  const cell = separatorCell.trim();
  if (cell.startsWith(":") && cell.endsWith(":")) {
    return "center";
  }
  if (cell.endsWith(":")) {
    return "right";
  }
  return "left";
}

function renderMarkdownTable(lines, startIndex) {
  const headers = splitMarkdownTableRow(lines[startIndex]);
  const separators = splitMarkdownTableRow(lines[startIndex + 1]);
  const alignments = separators.map(getMarkdownTableAlign);
  const rows = [];
  let index = startIndex + 2;

  while (index < lines.length) {
    const cells = splitMarkdownTableRow(lines[index]);
    if (cells.length !== headers.length) {
      break;
    }

    rows.push(cells);
    index += 1;
  }

  const colCount = headers.length;
  const headHtml = headers
    .map((cell, columnIndex) => {
      const align = alignments[columnIndex] || "left";
      return `<th style="text-align: ${align}">${renderInlineMarkdown(cell)}</th>`;
    })
    .join("");
  const bodyHtml = rows
    .map((row) => {
      const cells = Array.from({ length: colCount }, (_, columnIndex) => row[columnIndex] || "");
      const rowHtml = cells
        .map((cell, columnIndex) => {
          const align = alignments[columnIndex] || "left";
          return `<td style="text-align: ${align}">${renderInlineMarkdown(cell)}</td>`;
        })
        .join("");
      return `<tr>${rowHtml}</tr>`;
    })
    .join("");

  return {
    html: `<div class="markdown-table-wrap"><table><thead><tr>${headHtml}</tr></thead><tbody>${bodyHtml}</tbody></table></div>`,
    nextIndex: index,
  };
}

function renderInlineMarkdown(text) {
  return escapeHtml(text)
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/\*([^*]+)\*/g, "<em>$1</em>")
    .replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
}

function calendarIcon() {
  return `
    <svg class="meta-icon" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M7 2h2v3h6V2h2v3h3v17H4V5h3V2Zm11 8H6v10h12V10ZM6 7v1h12V7H6Z"></path>
    </svg>
  `;
}

function pathIcon() {
  return `
    <svg class="meta-icon" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M10.6 3 13 5.4V9h3.6L19 11.4V21H5V3h5.6Zm.8 2H7v14h10v-6h-6V5Zm1.6 1.4V11h4.6L13 6.4Z"></path>
    </svg>
  `;
}

window.renderMarkdown = renderMarkdown;
