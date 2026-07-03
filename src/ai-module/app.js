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

const exportState = {
  target: {
    type: "conversation",
    messageIndex: null,
    historyId: null,
  },
};

const elements = {
  appShell: document.getElementById("appShell"),
  modalTitle: document.getElementById("modalTitle"),
  resultModal: document.getElementById("resultModal"),
  historyModal: document.getElementById("historyModal"),
  exportModal: document.getElementById("exportModal"),
  clearConfirmModal: document.getElementById("clearConfirmModal"),
  modelPicker: document.getElementById("modelPicker"),
  modelSelectButton: document.getElementById("modelSelectButton"),
  modelMenu: document.getElementById("modelMenu"),
  currentModelName: document.getElementById("currentModelName"),
  currentModelTag: document.getElementById("currentModelTag"),
  modelKindIcon: document.getElementById("modelKindIcon"),
  openSelectorButton: document.getElementById("openSelectorButton"),
  openExportButton: document.getElementById("openExportButton"),
  openHistoryButton: document.getElementById("openHistoryButton"),
  refreshResultsButton: document.getElementById("refreshResultsButton"),
  closeModalButton: document.getElementById("closeModalButton"),
  confirmSelectionButton: document.getElementById("confirmSelectionButton"),
  closeHistoryButton: document.getElementById("closeHistoryButton"),
  closeExportButton: document.getElementById("closeExportButton"),
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
  exportStatus: document.getElementById("exportStatus"),
  exportFormatButtons: Array.from(document.querySelectorAll("[data-export-format]")),
  tabs: Array.from(document.querySelectorAll(".tabs button")),
  chatForm: document.getElementById("chatForm"),
  questionInput: document.getElementById("questionInput"),
  messages: document.getElementById("messages"),
  quickActions: Array.from(document.querySelectorAll(".quick-actions button")),
  toast: document.getElementById("toast"),
};

let toastTimer = null;
let isGenerating = false;
let isExporting = false;

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
  elements.openExportButton.addEventListener("click", openExportModal);
  elements.openHistoryButton.addEventListener("click", openHistoryModal);
  elements.refreshResultsButton.addEventListener("click", refreshResults);
  elements.closeModalButton.addEventListener("click", () => closeModal(elements.resultModal));
  elements.confirmSelectionButton.addEventListener("click", confirmSelection);
  elements.closeHistoryButton.addEventListener("click", () => closeModal(elements.historyModal));
  elements.closeExportButton.addEventListener("click", () => closeModal(elements.exportModal));
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

  elements.exportFormatButtons.forEach((button) => {
    button.addEventListener("click", () => exportConversation(button.dataset.exportFormat));
  });

  [elements.resultModal, elements.historyModal, elements.exportModal, elements.clearConfirmModal].forEach((modal) => {
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
      if (button.dataset.reportAction) {
        askQuestion(buildReportPrompt(), { exportKind: "report" });
        return;
      }

      askQuestion(button.dataset.question);
    });
  });

  elements.messages.addEventListener("click", (event) => {
    const button = event.target.closest("[data-empty-question]");
    if (button) {
      askQuestion(button.dataset.emptyQuestion);
      return;
    }

    const exportButton = event.target.closest("[data-export-message-index]");
    if (exportButton) {
      openExportModalForMessage(Number(exportButton.dataset.exportMessageIndex));
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
  updateSelectorTitle();
  renderResultList(elements.modalResultList);
  updateSelectorHint();
}

function updateSelectorTitle() {
  elements.modalTitle.textContent = `选择待分析结果（${resultState.draftSelected.size}）`;
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
      display_content: message.display_content || "",
      reasoning: message.reasoning || "",
      created_at: message.created_at || "",
      model: message.model || "",
      is_error: Boolean(message.is_error),
      export_kind: message.export_kind || "",
    }));
}

async function saveCurrentHistory() {
  const hasUserMessage = conversationState.messages.some((message) => message.role === "user");
  if (!hasUserMessage) {
    return null;
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
    return conversationState.id;
  } catch (error) {
    showToast("历史记录保存失败", "warning");
    return null;
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
      display_content: String(message.display_content || ""),
      reasoning: String(message.reasoning || ""),
      created_at: message.created_at || "",
      model: message.model || "",
      is_error: Boolean(message.is_error),
      export_kind: message.export_kind || "",
    }));
}

function renderConversationMessages() {
  if (conversationState.messages.length === 0) {
    resetMessagesToInitial();
    return;
  }

  elements.messages.classList.remove("empty");
  elements.messages.innerHTML = "";

  conversationState.messages.forEach((message, index) => {
    if (message.role === "user") {
      addUserMessage(getMessageDisplayContent(message), message.created_at || "时间待同步");
    }

    if (message.role === "assistant") {
      addAssistantMessage(message, index);
    }
  });
}

async function askQuestion(question, options = {}) {
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
    display_content: options.exportKind === "report" ? "【生成报告】" : "",
    created_at: questionTime,
  };

  ensureChatStarted();
  addUserMessage(getMessageDisplayContent(userMessage), questionTime);
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
    const assistantMessage = {
      role: "assistant",
      content: answer.content,
      reasoning: answer.reasoning,
      created_at: completedAt,
      model: currentModel,
      export_kind: options.exportKind || "",
    };
    conversationState.messages.push(assistantMessage);
    const assistantIndex = conversationState.messages.length - 1;
    replaceLoadingMessage(loadingId, {
      ...answer,
      completedAt,
      isFinal: true,
      messageIndex: assistantIndex,
      exportKind: assistantMessage.export_kind,
    });
    await saveCurrentHistory();
    if (options.exportKind === "report") {
      setGeneratingState(false);
      openExportModalForMessage(assistantIndex);
    }
  } catch (error) {
    const completedAt = formatMessageTime(new Date());
    const errorContent = error.message || "请检查 Flask 服务是否已启动，以及 DeepSeek API 配置是否可用。";
    const assistantMessage = {
      role: "assistant",
      content: errorContent,
      reasoning: "后端问答接口调用失败。",
      created_at: completedAt,
      model: currentModel,
      is_error: true,
    };
    conversationState.messages.push(assistantMessage);
    const assistantIndex = conversationState.messages.length - 1;
    replaceLoadingMessage(loadingId, {
      reasoning: "后端问答接口调用失败。",
      content: errorContent,
      completedAt,
      isFinal: true,
      keepReasoningOpen: true,
      messageIndex: assistantIndex,
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
  const exportButton = answer.isFinal ? buildAssistantExportButton(answer.messageIndex, answer.exportKind, Boolean(answer.is_error)) : "";
  const completedAt = answer.completedAt ? buildAssistantMessageFooter(answer.completedAt, exportButton) : "";

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

function addAssistantMessage(message, messageIndex) {
  const article = document.createElement("article");
  article.className = "message ai-message";
  const model = message.model || currentModel;
  const exportButton = buildAssistantExportButton(messageIndex, message.export_kind, Boolean(message.is_error));
  const completedAt = message.created_at ? buildAssistantMessageFooter(message.created_at, exportButton) : "";
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

function buildAssistantMessageFooter(timeText, exportButton) {
  return `
    <div class="message-footer">
      <div class="message-time-row">
        <div class="message-time">${escapeHtml(timeText)}</div>
        ${exportButton}
      </div>
      <div class="ai-content-disclaimer"><em>该内容由AI生成，请注意甄别</em></div>
    </div>
  `;
}

function buildAssistantExportButton(messageIndex, exportKind, isError) {
  if (!Number.isInteger(messageIndex) || isError) {
    return "";
  }

  const label = exportKind === "report" ? "导出报告" : "导出本段对话";
  return `<button class="message-export-button" type="button" data-export-message-index="${messageIndex}">${label}</button>`;
}

async function clearChat() {
  const historyId = conversationState.id;

  conversationState.id = null;
  conversationState.messages = [];
  resetMessagesToInitial();
  closeModal(elements.clearConfirmModal);
  showToast("对话已清空");

  if (!historyId) {
    return;
  }

  try {
    const response = await fetch(`/api/history/${encodeURIComponent(historyId)}`, {
      method: "DELETE",
    });

    if (!response.ok && response.status !== 404) {
      throw new Error("history delete unavailable");
    }

    historyState.records = historyState.records.filter((record) => record.id !== historyId);
    renderHistoryList();
  } catch (error) {
    showToast("对话已清空，但历史记录删除失败", "warning");
  }
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

function openExportModal() {
  if (isExporting) {
    showToast("正在导出，请稍候", "warning");
    return;
  }

  if (isGenerating) {
    showToast("请等待模型回答完成", "warning");
    return;
  }

  if (!conversationState.messages.some((message) => message.role === "user")) {
    showToast("当前还没有可导出的对话", "warning");
    return;
  }

  exportState.target = {
    type: "conversation",
    messageIndex: null,
    historyId: null,
  };
  setExportStatus("");
  openModal(elements.exportModal);
}

async function openExportModalForMessage(messageIndex) {
  if (isGenerating) {
    showToast("请等待模型回答完成", "warning");
    return;
  }

  const message = conversationState.messages[messageIndex];
  if (!message || message.role !== "assistant") {
    showToast("无法定位待导出的对话", "warning");
    return;
  }

  exportState.target = {
    type: message.export_kind === "report" ? "report" : "round",
    messageIndex,
    historyId: null,
  };
  setExportStatus("");

  try {
    await prepareExportHistory();
    openModal(elements.exportModal);
  } catch (error) {
    showToast("导出记录生成失败", "warning");
  }
}

function openResultModal() {
  resultState.draftSelected = new Map(resultState.selected);
  renderResultLists();
  openModal(elements.resultModal);
}

async function exportConversation(fileFormat) {
  if (isExporting) {
    return;
  }

  setExportingState(true);
  setExportStatus("");
  showToast("正在导出...", "warning");

  try {
    const historyId = await prepareExportHistory();
    if (!historyId) {
      throw new Error("history save unavailable");
    }

    const response = await fetch(`/api/history/${encodeURIComponent(historyId)}/export`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        format: fileFormat,
      }),
    });

    if (!response.ok) {
      throw new Error("export api unavailable");
    }

    const exportResult = await response.json();
    resetTempExportHistoryAfterUse();
    const exportedFile = exportResult.files?.[fileFormat];
    if (!exportedFile?.download_url) {
      throw new Error("export file unavailable");
    }

    setExportStatus("导出成功！");
    showToast("导出成功！");
    triggerBrowserDownload(exportedFile.download_url, exportedFile.name);
  } catch (error) {
    setExportStatus("导出失败，请检查导出程序和后端状态。");
    showToast("导出失败", "warning");
  } finally {
    resetTempExportHistoryAfterUse();
    setExportingState(false);
  }
}

function resetTempExportHistoryAfterUse() {
  if (exportState.target.type !== "conversation") {
    exportState.target.historyId = null;
  }
}

async function prepareExportHistory() {
  if (exportState.target.type === "conversation") {
    return saveCurrentHistory();
  }

  if (exportState.target.historyId) {
    return exportState.target.historyId;
  }

  const history = buildMessageExportHistory(exportState.target.messageIndex, exportState.target.type);
  if (!history) {
    return null;
  }

  const savedHistoryId = await saveExportHistory(history);
  exportState.target.historyId = savedHistoryId;
  return savedHistoryId;
}

function buildMessageExportHistory(messageIndex, exportKind) {
  const assistantMessage = conversationState.messages[messageIndex];
  if (!assistantMessage || assistantMessage.role !== "assistant") {
    return null;
  }

  const userIndex = findPreviousUserMessageIndex(messageIndex);
  if (userIndex < 0) {
    return null;
  }

  const userMessage = conversationState.messages[userIndex];
  const now = formatBackendTime(new Date());
  const idPrefix = exportKind === "report" ? "report" : "round";
  return {
    id: `${idPrefix}_${createExportTimestamp()}`,
    export_kind: exportKind,
    created_at: userMessage.created_at || now,
    updated_at: now,
    model: assistantMessage.model || currentModel,
    selected_results: Array.from(resultState.selected.values()),
    messages: [
      normalizeMessageForExport(userMessage),
      normalizeMessageForExport(assistantMessage),
    ],
  };
}

function findPreviousUserMessageIndex(messageIndex) {
  for (let index = messageIndex - 1; index >= 0; index -= 1) {
    if (conversationState.messages[index]?.role === "user") {
      return index;
    }
  }

  return -1;
}

function normalizeMessageForExport(message) {
  return {
    role: message.role,
    content: message.content,
    display_content: message.display_content || "",
    reasoning: message.reasoning || "",
    created_at: message.created_at || "",
    model: message.model || "",
    is_error: Boolean(message.is_error),
    export_kind: message.export_kind || "",
  };
}

function getMessageDisplayContent(message) {
  return message.display_content || message.content || "";
}

async function saveExportHistory(history) {
  const response = await fetch("/api/history/save", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(history),
  });

  if (!response.ok) {
    throw new Error("history save unavailable");
  }

  const data = await response.json();
  return data.id || data.history?.id || history.id;
}

function setExportingState(exporting) {
  isExporting = exporting;
  elements.openExportButton.setAttribute("aria-disabled", String(exporting));
  elements.exportFormatButtons.forEach((button) => {
    button.disabled = exporting;
  });
}

function setExportStatus(text) {
  elements.exportStatus.textContent = text;
}

function triggerBrowserDownload(url, fileName) {
  const link = document.createElement("a");
  link.href = url;
  link.download = fileName || "";
  link.style.display = "none";
  document.body.appendChild(link);
  link.click();
  link.remove();
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

function formatBackendTime(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  const seconds = String(date.getSeconds()).padStart(2, "0");
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
}

function createExportTimestamp() {
  const now = new Date();
  const milliseconds = String(now.getMilliseconds()).padStart(3, "0");
  return `${formatBackendTime(now).replace(/[-: ]/g, "")}_${milliseconds}`;
}

function buildReportPrompt() {
  const selectedFiles = Array.from(resultState.selected.values());
  const fileNames = selectedFiles.length
    ? selectedFiles.map((file, index) => `${index + 1}. ${file.name || file.path || "未命名文件"}`).join("\n")
    : "当前未选择分析文件";

  return `请根据当前选择的分析文件生成一份较为正式、结构完整、可直接导出的电商数据分析报告。

报告要求：
1. 使用正式的 Markdown 格式输出，标题、摘要、关键发现、数据解读、业务建议、风险与后续动作等结构清晰。
2. 报告正文必须明确提到本次分析使用的文件名。
3. 内容应面向业务使用者，结论、推断和建议需要区分清楚。
4. 这份 Markdown 将直接提供给用户导出，请不要输出闲聊式开场白，不要说明“下面是报告”，直接从报告标题开始。
5. 不要在末尾添加模型声明或生成时间，系统会在导出时自动补充。
6. 如果文件上下文标注为“已完整提供，未截断”，不要声称存在“部分数据未展示”“仅提供部分明细”等限制；对于推荐类 JSON，要按上下文里的结构摘要区分顶层群组数和群组内商品推荐明细数。
7. 如需展示结构化结果，必须使用标准 Markdown 表格：表格前后各留一个空行；第二行必须是“| --- | --- |”这类分隔行；不要把表格放进代码块、引用块或列表项里；每一行都必须以“|”开头和结尾。

本次分析文件：
${fileNames}`;
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
