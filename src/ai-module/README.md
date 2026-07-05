# 电商数据智能分析助手 v4

本模块是AI模块“电商数据智能分析助手”的前后端实现，用于读取项目已生成的分析结果文件，并通过 DeepSeek API 进行流式问答和结果解读。

## 更新日志

- v4：Windows 导出适配与打包优化
```text
1. 适配 Windows 端 Word / PDF 转换路径。
2. 支持用户按需选择导出 Markdown、Word 或 PDF 文件，避免每次生成全部格式。
3. 优化 AI 对话和 AI 报告的导出流程。
4. 补充 PyInstaller 打包脚本，便于将 AI 模块后端打包为可执行程序。
5. 打包时自动收集前端资源、pandoc / docx 相关依赖，并复制 result 数据目录。
```

- v3：新增报告导出与上下文增强
```text
1. 新增当前对话、单轮对话和分析报告导出前端入口。
2. 新增 `output.py` 导出程序，用于生成 md / docx / pdf 文件。
3. 优化 Markdown 表格格式，改善 Word / PDF 排版效果。
4. 调整历史记录与导出文件存储目录至 `result/ai/`。
5. 新增生成报告快捷指令和报告专用导出逻辑。
6. 扩充传给模型的文件上下文，完善 JSON 结构摘要。
7. 增加 AI 内容甄别提示和 Word / PDF 导出依赖提示。
```

- v2：限制分析文件类型，改善体验
```text
 1.限制可分析文件类型为csv, markdown, json，增加内容解析和前端文件类型校验
 2.文件选择器增加显示已选文件数量，新增支持格式提示，新增删除历史记录提示
 3.修复清除对话后，对话历史文件没有删除的bug
 4.重绘对话框关闭按钮，修复按钮显示异常bug
```
- v1：基本功能构建完成，第一次发版

## 模块功能

### 1. 选择待分析结果

用户进入助手前，可在欢迎页选择项目生成的分析报告、模型结果或推荐结果文件。系统会将所选文件内容作为上下文传给 DeepSeek 模型。

### 2. DeepSeek 流式问答

用户可以在聊天页面输入自然语言问题，后端会将用户问题、已选文件上下文和多轮对话历史组装为 messages，并调用 DeepSeek API。

AI 回答采用流式返回方式，前端实时展示生成结果。

### 3. 多轮对话

前端维护用户与 AI 助手的历史消息，后端每次请求时重新组装多轮对话上下文，使 AI 能够基于当前对话继续回答。

### 4. 模型连接状态检测

用户进入系统或切换模型时，前端会调用模型状态接口，检测 DeepSeek API 是否能够正常连接。

### 5. 历史对话管理

系统会自动保存历史对话记录，包括：

- 对话 ID；
- 创建时间；
- 更新时间；
- 使用模型；
- 已选分析文件；
- 用户问题；
- AI 回答内容。

用户可以在欢迎页或聊天页重新载入历史对话，也可以删除不需要的历史记录。

### 6. Markdown 渲染

前端支持常见 Markdown 内容展示，包括：

- 标题；
- 列表；
- 加粗文本；
- 代码块；
- 表格；
- 分隔线。

针对 AI 回答中的 Markdown 表格，系统提示词要求模型输出标准 Markdown 表格格式，以减少网页渲染和文档导出时的格式错乱。

### 7. AI 分析报告生成

系统内置报告生成快捷指令，能够根据用户选择的分析文件生成较正式的分析报告。报告内容可包括：

- 数据概况；
- 主要发现；
- 用户行为分析；
- 商品推荐分析；
- 运营建议；
- 局限性与改进方向。

### 8. 文件导出

系统支持将 AI 对话或 AI 分析报告导出为以下格式：

- Markdown：`.md`
- Word：`.docx`
- PDF：`.pdf`

导出文件可通过浏览器进行下载。


## 目录结构

```text
src/ai-module/
├─ backend.py              # Flask 后端接口与 DeepSeek API 调用
├─ output.py               # AI 对话和 AI 报告导出程序
├─ welcome.html            # 欢迎页，选择分析文件或历史对话
├─ welcome.css
├─ welcome.js
├─ index.html              # AI 聊天页面
├─ styles.css
├─ app.js                  # 前端交互逻辑
├─ pack.ps1                # PyInstaller 打包脚本
└─ README.md
```

模块运行时会读取或写入以下项目目录：

```text
result/
├─ reports/                # 分析报告，供 AI 读取
├─ models/                 # 模型结果、推荐结果，供 AI 读取
└─ ai/
   ├─ ai-history/          # AI 历史对话 JSON 文件
   └─ ai-output/           # AI 导出的 md / docx / pdf 文件
```

⚠️注意：因DeepSeek限制，API不支持读取图片，故本模块不读取`result/figures`目录。

## 分析文件类型说明

### 分析报告

目录：`result/reports/`

前端会展示该目录下的报告文件。后端可读取并传给 DeepSeek 的文本类文件包括：

- `.md`
- `.json`

当前项目主要使用 `.md` 分析报告，例如 `step2_analysis_report.md`。

### 模型结果

目录：`result/models/`

AI 模块当前仅支持选择和分析 CSV 表格文件。

例如：

- `cluster_profiles.csv`
- `frequent_itemsets.csv`
- `association_rules.csv`

`pkl`、`pickle`、`joblib` 等二进制模型文件**不会**在 AI 模块中作为“模型结果”展示，也不会传给 DeepSeek 分析。


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

1. 打开 AI 智能分析助手欢迎页。
2. 在页面中选择需要分析的报告文件、模型结果文件或推荐结果文件。
3. 点击“开始智能分析”进入聊天页面。
4. 在聊天页面中输入自然语言问题，或点击快捷指令。
5. AI 根据已选文件内容生成分析回答。
6. 系统自动保存历史对话。
7. 如需继续分析，可追加文件或载入历史记录。
8. 如需提交或保存结果，可导出 Markdown、Word 或 PDF 文件。

## 后端接口说明 

| 接口                                             | 方法   | 作用                           |
| ------------------------------------------------ | ------ | ------------------------------ |
| `/`                                              | GET    | 打开欢迎页                     |
| `/api/results`                                   | GET    | 获取可供 AI 分析的结果文件列表 |
| `/api/chat`                                      | POST   | 调用 DeepSeek API 进行流式问答 |
| `/api/model-status`                              | POST   | 检测模型连接状态               |
| `/api/history`                                   | GET    | 获取历史对话摘要列表           |
| `/api/history/<history_id>`                      | GET    | 读取指定历史对话详情           |
| `/api/history/<history_id>`                      | DELETE | 删除指定历史对话               |
| `/api/history/save`                              | POST   | 保存或更新历史对话             |
| `/api/history/<history_id>/export`               | POST   | 导出历史对话或 AI 分析报告     |
| `/api/history/<history_id>/export/<file_format>` | GET    | 下载指定格式的导出文件         |

## 注意事项

- DeepSeek Chat API 本身是无状态接口，多轮对话需要每次请求都传入历史消息，本模块已在前后端完成适配。
- 历史记录会随着每次用户提问自动保存。
- 当前模块不支持图片、图表和二进制模型文件解析。
- 模型结果只支持 CSV 文件；如需让 AI 理解模型输出，请优先导出为 CSV 或写入 Markdown 报告。
