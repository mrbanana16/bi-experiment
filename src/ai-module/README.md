# 电商数据智能分析助手 v1

本模块是AI模块“电商数据智能分析助手”的前后端实现，用于读取项目已生成的分析结果文件，并通过 DeepSeek API 进行流式问答、结果解读和历史对话管理。

## 更新日志

- v1：基本功能构建完成，第一次发版

## 模块功能

- 选择待分析结果：进入助手前可选择分析报告和模型结果。
- DeepSeek 流式问答：通过 `/api/chat` 将用户问题、已选文件上下文和多轮对话历史传给 DeepSeek，并流式返回回答。
- 多轮对话：前端维护 `user/assistant` 历史，后端按 DeepSeek 多轮对话格式重新组装 `messages`。
- 模型连通性检测：切换模型或初次进入时检测 DeepSeek API 连接状态。
- 历史对话：每次用户提问并收到回答后自动保存历史记录，可从欢迎页或聊天页重新载入。
- Markdown 渲染：支持标题、列表、代码块、表格等常见 Markdown 内容展示。

## 目录结构

```text
src/ai-module/
├─ backend.py       # 模块后端文件，Flask 后端接口与 DeepSeek API 调用
├─ welcome.html     # 前端欢迎页进入助手前的文件选择页面
├─ welcome.css
├─ welcome.js
├─ index.html       # 前端 AI 聊天页面
├─ styles.css
├─ app.js
└─ README.md
```

模块运行时会读取或写入以下项目目录：

```text
result/
├─ reports/         # 分析报告（读取）
├─ models/          # 模型结果（读取）
└─ ai-history/      # AI 对话历史 JSON（读取，写入）
```

⚠️注意：因DeepSeek限制，API不支持读取图片，故本模块不读取`result/figures`目录。

## 支持分析的文件类型

### 分析报告

目录：`result/reports/`

前端会展示该目录下的报告文件。后端可读取并传给 DeepSeek 的文本类文件包括：

- `.md`
- `.txt`
- `.json`
- `.log`
- `.py`
- `.html`
- `.js`

当前项目主要使用 `.md` 分析报告，例如 `step2_analysis_report.md`。

### 模型结果

目录：`result/models/`

AI 模块当前仅支持选择和分析 CSV 表格文件：

- `.csv`

例如：

- `cluster_profiles.csv`
- `frequent_itemsets.csv`
- `association_rules.csv`

`pkl`、`pickle`、`joblib` 等二进制模型文件**不会**在 AI 模块中作为“模型结果”展示，也不会传给 DeepSeek 分析。

### 图表文件

目录：`result/figures/`

当前 AI 模块不支持图表/图片识别，因此不会读取或分析 `.png` 等图表文件。如需分析图表内容，请先在报告或 CSV 文件中提供对应的文字化结果。

### 历史对话

目录：`result/ai-history/`

历史对话保存为 `.json` 文件，由 AI 模块自动创建和更新。历史列表接口只返回首个用户问题、选择的分析文件、对话发生时间等摘要信息；读取详情时才返回完整对话内容。

当前仓库中有一份示例历史对话，可点击该对话查看。

## 使用方法

### 1.安装依赖

根据项目总`README.md`文件，安装`requirements.txt`里的所有依赖。

### 2.配置 DeepSeek API Key

在`backend.py`的变量中输入DeepSeek API Key。

**❗️注意：commit之前务必检查，不要将api key提交到远程仓库！**

### 3. 启动后端

运行`backend.py`文件，启动 Flask 服务：

```bash
python backend.py
```

默认服务地址：

```text
http://127.0.0.1:9090
```

### 4. 访问页面

使用浏览器访问：

```text
http://127.0.0.1:9090/
```

即可自动跳转到欢迎页，开始使用系统。

使用流程：

1. 在欢迎页选择待分析结果，或选择一条历史对话记录继续对话。
2. 点击“开始智能分析”进入聊天页。
3. 在聊天页输入问题，或使用快捷指令。
4. 如需追加文件，点击“补充文件”。

## 后端接口 `/api/results`

读取项目 `result/` 目录下可供 AI 分析的结果文件。

返回内容包括：

- 文件名
- 文件创建日期
- 文件路径
- 文件类型

### 1. `/api/chat`

调用 DeepSeek API 的流式问答接口。

请求内容包括：

- `model`：模型名称，支持 `deepseek-v4-pro` 和 `deepseek-v4-flash`
- `question`：用户本轮问题
- `selected_results`：当前选择的分析文件
- `conversation_history`：历史 `user/assistant` 消息

返回格式为 SSE 流，前端按 `reasoning` 和 `content` 分区展示。

### 2. `/api/model-status`

检测指定 DeepSeek 模型连接状态，用于前端显示连接中、连接成功或连接失败。

### 3. `/api/history`

读取 `result/ai-history/` 下的历史对话摘要列表。

### 4. `/api/history/<history_id>`

读取指定历史对话详情。`history_id` 为历史文件名去掉 `.json` 后的名称。

### 5. `/api/history/save`

保存当前对话历史。若传入已有 `id`，则更新对应历史文件；若未传入 `id`，则新建历史 JSON 文件。

## 注意事项

- DeepSeek Chat API 本身是无状态接口，多轮对话需要每次请求都传入历史消息，本模块已在前后端完成适配。
- 历史记录会随着每次用户提问自动保存。
- 当前模块不支持图片、图表和二进制模型文件解析。
- 模型结果只支持 CSV 文件；如需让 AI 理解模型输出，请优先导出为 CSV 或写入 Markdown 报告。
