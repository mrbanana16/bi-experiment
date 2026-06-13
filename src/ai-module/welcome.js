const SELECTED_RESULTS_STORAGE_KEY = "aiModuleSelectedResults";
const HISTORY_RECORD_STORAGE_KEY = "aiModuleHistoryRecord";

const resultState = {
  activeTab: "reports",
  selected: new Map(),
  results: {
    reports: [],
    models: [],
  },
  demoMode: false,
  loadError: false,
};

const elements = {
  welcomeScreen: document.getElementById("welcomeScreen"),
  welcomeResultList: document.getElementById("welcomeResultList"),
  welcomeBackendStatus: document.getElementById("welcomeBackendStatus"),
  welcomeHistoryModal: document.getElementById("welcomeHistoryModal"),
  welcomeHistoryList: document.getElementById("welcomeHistoryList"),
  welcomeHistoryStatus: document.getElementById("welcomeHistoryStatus"),
  startAnalysisButton: document.getElementById("startAnalysisButton"),
  openHistoryButton: document.getElementById("openHistoryButton"),
  welcomeRefreshResultsButton: document.getElementById("welcomeRefreshResultsButton"),
  welcomeRefreshHistoryButton: document.getElementById("welcomeRefreshHistoryButton"),
  welcomeCloseHistoryButton: document.getElementById("welcomeCloseHistoryButton"),
  tabs: Array.from(document.querySelectorAll(".tabs button")),
  toast: document.getElementById("toast"),
};

let toastTimer = null;
let historyRecords = [];
let historyLoadError = false;

document.addEventListener("DOMContentLoaded", () => {
  bindEvents();
  loadResults();
});

function bindEvents() {
  elements.startAnalysisButton.addEventListener("click", enterAssistant);
  elements.openHistoryButton.addEventListener("click", openHistoryModal);
  elements.welcomeRefreshResultsButton.addEventListener("click", refreshResults);
  elements.welcomeRefreshHistoryButton.addEventListener("click", () => loadHistoryList(true));
  elements.welcomeCloseHistoryButton.addEventListener("click", () => closeModal(elements.welcomeHistoryModal));

  elements.welcomeHistoryModal.addEventListener("click", (event) => {
    if (event.target === elements.welcomeHistoryModal) {
      closeModal(elements.welcomeHistoryModal);
    }
  });

  elements.welcomeHistoryList.addEventListener("click", (event) => {
    const historyButton = event.target.closest("[data-history-id]");
    if (historyButton) {
      enterAssistantFromHistory(historyButton.dataset.historyId);
    }
  });

  elements.tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      resultState.activeTab = tab.dataset.tab;
      renderTabs();
      renderResultList();
    });
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
    resultState.demoMode = false;
    resultState.loadError = true;
    setBackendStatus("读取 result 目录失败，请确认后端 /api/results 已启动。");
  }

  renderTabs();
  renderResultList();
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

function setBackendStatus(text) {
  elements.welcomeBackendStatus.textContent = text;
}

function reconcileSelectedResults() {
  const nextSelected = new Map();

  for (const [key, file] of resultState.selected.entries()) {
    const currentFile = findFileByKey(key);
    if (currentFile) {
      nextSelected.set(key, currentFile);
    }
  }

  resultState.selected = nextSelected;
}

function renderTabs() {
  elements.tabs.forEach((tab) => {
    tab.classList.toggle("active", tab.dataset.tab === resultState.activeTab);
  });
}

function renderResultList() {
  const files = resultState.results[resultState.activeTab] || [];

  if (files.length === 0) {
    elements.welcomeResultList.innerHTML = `<div class="empty-state">${getEmptyStateText()}</div>`;
    updateSelectorHint();
    return;
  }

  elements.welcomeResultList.innerHTML = files
    .map((file) => {
      const fileKey = getFileKey(resultState.activeTab, file);
      const checked = resultState.selected.has(fileKey) ? "checked" : "";
      const name = escapeHtml(file.name || file.path || "未命名结果");
      const path = escapeHtml(file.path || file.name || "");
      const createdAt = escapeHtml(formatDate(file.created_at));

      return `
        <div class="result-item">
          <label>
            <input type="checkbox" data-key="${escapeHtml(fileKey)}" ${checked}>
            <span class="file-content">
              <span class="file-name">${name}</span>
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

  elements.welcomeResultList.querySelectorAll("input[type='checkbox']").forEach((checkbox) => {
    checkbox.addEventListener("change", () => toggleSelection(checkbox));
  });

  updateSelectorHint();
}

function getEmptyStateText() {
  if (resultState.activeTab === "models") {
    return "当前分类暂无可选择 CSV 模型结果。";
  }

  return "当前分类暂无可选择结果。";
}

async function refreshResults() {
  await loadResults();
  showToast("文件列表已刷新");
}

async function openHistoryModal() {
  await loadHistoryList();
  openModal(elements.welcomeHistoryModal);
}

async function loadHistoryList(showSuccessToast = false) {
  try {
    const response = await fetch("/api/history");
    if (!response.ok) {
      throw new Error("history api unavailable");
    }

    const data = await response.json();
    historyRecords = Array.isArray(data.history) ? data.history : [];
    historyLoadError = false;
    setHistoryStatus("");
    renderHistoryList();
    if (showSuccessToast) {
      showToast("历史记录已刷新");
    }
  } catch (error) {
    historyRecords = [];
    historyLoadError = true;
    setHistoryStatus("读取历史记录失败，请确认后端 /api/history 已启动。");
    renderHistoryList();
  }
}

function renderHistoryList() {
  if (historyLoadError) {
    elements.welcomeHistoryList.innerHTML = `<div class="empty-state">历史记录读取失败。</div>`;
    return;
  }

  if (historyRecords.length === 0) {
    elements.welcomeHistoryList.innerHTML = `<div class="empty-state">当前暂无历史对话。</div>`;
    return;
  }

  elements.welcomeHistoryList.innerHTML = historyRecords
    .map((record) => `
      <button class="history-item" type="button" data-history-id="${escapeHtml(record.id)}">
        <span class="history-title">${escapeHtml(record.first_question || "未命名历史对话")}</span>
        <span class="history-meta">
          <span>${calendarIcon()}${escapeHtml(record.created_at || "时间待同步")}</span>
          <span>${pathIcon()}${escapeHtml(formatHistoryFiles(record.selected_files || record.selected_results || []) || "未记录分析文件")}</span>
        </span>
      </button>
    `)
    .join("");
}

async function enterAssistantFromHistory(historyId) {
  if (!historyId) {
    return;
  }

  try {
    const response = await fetch(`/api/history/${encodeURIComponent(historyId)}`);
    if (!response.ok) {
      throw new Error("history detail unavailable");
    }

    const data = await response.json();
    const history = data.history || data;
    sessionStorage.setItem(HISTORY_RECORD_STORAGE_KEY, JSON.stringify(history));
    sessionStorage.setItem(SELECTED_RESULTS_STORAGE_KEY, JSON.stringify(history.selected_results || []));
    elements.welcomeScreen.classList.add("leaving");

    window.setTimeout(() => {
      window.location.href = "./index.html";
    }, 220);
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
    .map((file) => `${file.name || file.path || "未命名结果"}`)
    .join("；");
  const rest = files.length > 2 ? ` 等 ${files.length} 个文件` : "";
  return `${preview}${rest}`;
}

function setHistoryStatus(text) {
  elements.welcomeHistoryStatus.textContent = text;
}

function openModal(modal) {
  modal.classList.remove("hidden", "closing");
}

function closeModal(modal) {
  if (modal.classList.contains("hidden") || modal.classList.contains("closing")) {
    return;
  }

  modal.classList.add("closing");
  window.setTimeout(() => {
    modal.classList.add("hidden");
    modal.classList.remove("closing");
  }, 170);
}

function updateSelectorHint() {
  if (resultState.loadError) {
    return;
  }

  setBackendStatus("");
}

function toggleSelection(checkbox) {
  const file = findFileByKey(checkbox.dataset.key);
  if (!file) {
    return;
  }

  if (checkbox.checked) {
    resultState.selected.set(checkbox.dataset.key, file);
  } else {
    resultState.selected.delete(checkbox.dataset.key);
  }

  renderResultList();
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

function enterAssistant() {
  if (resultState.selected.size === 0) {
    showToast("请先选择至少一个分析结果", "warning");
    return;
  }

  const selectedResults = Array.from(resultState.selected.values());
  sessionStorage.setItem(SELECTED_RESULTS_STORAGE_KEY, JSON.stringify(selectedResults));
  elements.welcomeScreen.classList.add("leaving");

  window.setTimeout(() => {
    window.location.href = "./index.html";
  }, 220);
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

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
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
