# https://zhuanlan.zhihu.com/p/79634564
import json
import os
import csv
from datetime import datetime
from pathlib import Path
import re

import httpx
from flask import Flask, Response, jsonify, request, stream_with_context
from openai import OpenAI

app = Flask(__name__, static_folder=".", static_url_path="")

### ------在下方输入deepseek api key------
DEEPSEEK_API_KEY = "sk-??????"
### ------输入api key后才能正常使用------
### 注意！！！commit之前务必检查，不要将api key上传到github！！！

DEEPSEEK_BASE_URL = "https://api.deepseek.com"
AVAILABLE_MODELS = {"deepseek-v4-pro", "deepseek-v4-flash"}
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULT_ROOT = PROJECT_ROOT / "result"
HISTORY_ROOT = RESULT_ROOT / "ai-history"
RESULT_CATEGORIES = {
    "reports": RESULT_ROOT / "reports",
    "models": RESULT_ROOT / "models",
}
TEXT_EXTENSIONS = {".md", ".txt", ".json", ".log", ".py", ".html", ".js"}
TABLE_EXTENSIONS = {".csv", ".tsv"}
MODEL_SELECTABLE_EXTENSIONS = {".csv"}
MAX_CONTEXT_CHARS = 60000
MAX_TEXT_FILE_CHARS = 12000
MAX_TABLE_ROWS = 30
MAX_HISTORY_MESSAGES = 20
MAX_HISTORY_MESSAGE_CHARS = 8000

SYSTEM_PROMPT = """
你是“电商数据智能分析助手”，一名熟悉电商用户行为、商品销售、用户分群、关联规则、转化漏斗和运营策略的数据分析专家。

你的任务：
1. 只依据用户本次选择的分析结果文件回答问题，不要主动引用未选择的其他结果文件。
2. 如果文件上下文不足以支撑结论，必须明确说明“当前文件信息不足”，再给出合理的分析思路或需要补充的数据。
3. 区分事实、推断和建议，不要编造文件中不存在的指标、字段或数值。
4. 回答应面向电商业务使用者，尽量给出可执行的运营建议、分析结论和下一步动作。
5. 使用中文回答，输出 Markdown 格式，结构清晰，必要时使用列表、表格和小标题。
6. 模型结果只支持 CSV 表格上下文；如果用户问题依赖未提供或不可解析的模型文件内容，需说明当前文件信息不足。
""".strip()

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_BASE_URL,
    http_client=httpx.Client(trust_env=False, timeout=20),
)


@app.get("/")
def index():
    return app.send_static_file("welcome.html")


@app.get("/api/results")
def results():
    return jsonify({"results": list_result_files()})


@app.get("/api/history")
def history_list():
    return jsonify({"history": list_history_records()})


@app.get("/api/history/<history_id>")
def history_detail(history_id):
    history_file = resolve_history_file(history_id)

    if not history_file or not history_file.exists():
        return jsonify({"error": "history not found"}), 404

    try:
        history = read_history_file(history_file)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    return jsonify({"history": history})


@app.post("/api/history/save")
def history_save():
    payload = request.get_json(silent=True) or {}
    history = save_history_record(payload)
    return jsonify({
        "id": history["id"],
        "history": history,
        "summary": summarize_history_record(history),
    })


@app.post("/api/model-status")
def model_status():
    payload = request.get_json(silent=True) or {}
    model = payload.get("model") or "deepseek-v4-pro"

    if model not in AVAILABLE_MODELS:
        return jsonify({
            "status": "error",
            "model": model,
            "message": "unsupported model",
        }), 400

    try:
        client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a connection test assistant."},
                {"role": "user", "content": "ping"},
            ],
            stream=False,
            max_tokens=1,
        )
    except Exception as error:
        return jsonify({
            "status": "error",
            "model": model,
            "message": str(error),
        }), 200

    return jsonify({
        "status": "success",
        "model": model,
        "message": "connected",
    })


def list_result_files():
    results = {}

    for category, directory in RESULT_CATEGORIES.items():
        files = []

        if directory.exists():
            category_files = [
                file_path
                for file_path in directory.rglob("*")
                if file_path.is_file() and not any(part.startswith(".") for part in file_path.relative_to(directory).parts)
            ]

            for file_path in sorted(category_files, key=lambda path: path.stat().st_mtime, reverse=True):
                if not file_path.is_file() or not is_selectable_result_file(category, file_path):
                    continue

                stat = file_path.stat()
                name = file_path.name
                path = file_path.relative_to(PROJECT_ROOT).as_posix()
                created_at = format_file_time(stat)
                files.append({
                    "name": name,
                    "file_name": name,
                    "type": category,
                    "file_type": category,
                    "category": category,
                    "path": path,
                    "file_path": path,
                    "created_at": created_at,
                    "file_created_at": created_at,
                    "size": stat.st_size,
                })

        results[category] = files

    return results


def is_selectable_result_file(category, file_path):
    if category == "models":
        return file_path.suffix.lower() in MODEL_SELECTABLE_EXTENSIONS

    return True


def format_file_time(stat):
    timestamp = getattr(stat, "st_birthtime", stat.st_mtime)
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


def list_history_records():
    HISTORY_ROOT.mkdir(parents=True, exist_ok=True)
    records = []

    for history_file in sorted(HISTORY_ROOT.glob("*.json"), key=lambda path: path.stat().st_mtime, reverse=True):
        if history_file.name.startswith("."):
            continue

        try:
            records.append(summarize_history_record(read_history_file(history_file)))
        except ValueError:
            continue

    return records


def read_history_file(history_file):
    try:
        with history_file.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("history file invalid") from error

    if not isinstance(data, dict):
        raise ValueError("history file invalid")

    data["id"] = sanitize_history_id(data.get("id") or history_file.stem) or history_file.stem
    data["file_name"] = history_file.name
    data["selected_results"] = normalize_selected_results(data.get("selected_results"))
    data["messages"] = normalize_history_messages(data.get("messages"))
    data["created_at"] = data.get("created_at") or format_file_time(history_file.stat())
    data["updated_at"] = data.get("updated_at") or format_file_time(history_file.stat())
    return data


def summarize_history_record(history):
    selected_results = normalize_selected_results(history.get("selected_results"))
    first_question = next(
        (message.get("content", "") for message in normalize_history_messages(history.get("messages")) if message.get("role") == "user"),
        "未命名历史对话",
    )
    selected_files = [
        {
            "type": file.get("type") or file.get("category") or "unknown",
            "name": file.get("name") or file.get("path") or "未命名结果",
            "path": file.get("path") or file.get("name") or "",
        }
        for file in selected_results
    ]

    return {
        "id": history.get("id") or "",
        "file_name": history.get("file_name") or f"{history.get('id', '')}.json",
        "first_question": first_question,
        "selected_results": selected_files,
        "selected_files": selected_files,
        "created_at": history.get("created_at") or "",
        "updated_at": history.get("updated_at") or "",
        "message_count": len(normalize_history_messages(history.get("messages"))),
    }


def save_history_record(payload):
    HISTORY_ROOT.mkdir(parents=True, exist_ok=True)
    raw_history_id = payload.get("id") or payload.get("history_id") or ""
    history_id = sanitize_history_id(raw_history_id) or create_history_id()
    history_file = HISTORY_ROOT / f"{history_id}.json"
    existing = {}

    if history_file.exists():
        existing = read_history_file(history_file)

    now = current_time_text()
    messages = payload.get("messages") if "messages" in payload else existing.get("messages")
    history = {
        "id": history_id,
        "file_name": history_file.name,
        "created_at": existing.get("created_at") or payload.get("created_at") or now,
        "updated_at": now,
        "model": payload.get("model") or existing.get("model") or "deepseek-v4-pro",
        "selected_results": normalize_selected_results(payload.get("selected_results") or existing.get("selected_results")),
        "messages": normalize_history_messages(messages),
    }

    with history_file.open("w", encoding="utf-8") as file:
        json.dump(history, file, ensure_ascii=False, indent=2)

    return history


def resolve_history_file(history_id):
    sanitized = sanitize_history_id(history_id)
    if not sanitized:
        return None

    return HISTORY_ROOT / f"{sanitized}.json"


def sanitize_history_id(history_id):
    if not history_id:
        return ""

    name = str(history_id).removesuffix(".json")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", name):
        return ""

    return name


def create_history_id():
    return f"history_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"


def current_time_text():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def normalize_selected_results(selected_results):
    if not isinstance(selected_results, list):
        return []

    normalized = []
    for file in selected_results:
        if not isinstance(file, dict):
            continue

        normalized.append({
            "type": file.get("type") or file.get("category") or file.get("file_type") or "unknown",
            "category": file.get("category") or file.get("type") or file.get("file_type") or "unknown",
            "name": file.get("name") or file.get("file_name") or file.get("path") or file.get("file_path") or "未命名结果",
            "path": file.get("path") or file.get("file_path") or file.get("name") or file.get("file_name") or "",
            "created_at": file.get("created_at") or file.get("file_created_at") or "",
            "supplemented": bool(file.get("supplemented")),
        })

    return normalized


def normalize_history_messages(messages):
    if not isinstance(messages, list):
        return []

    normalized = []
    for message in messages:
        if not isinstance(message, dict):
            continue

        role = message.get("role")
        if role not in {"user", "assistant"}:
            continue

        content = str(message.get("content") or "")[:MAX_HISTORY_MESSAGE_CHARS]
        if not content:
            continue

        normalized.append({
            "role": role,
            "content": content,
            "reasoning": str(message.get("reasoning") or "")[:MAX_HISTORY_MESSAGE_CHARS],
            "created_at": message.get("created_at") or "",
            "model": message.get("model") or "",
            "is_error": bool(message.get("is_error")),
        })

    return normalized


def build_messages(question, selected_results, conversation_history=None):
    file_context = build_selected_file_context(selected_results)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    for history_message in build_api_history_messages(conversation_history):
        messages.append(history_message)

    messages.append({"role": "user", "content": build_user_prompt(question, file_context)})
    return messages


def build_api_history_messages(conversation_history):
    normalized = normalize_history_messages(conversation_history)
    normalized = [message for message in normalized if not message.get("is_error")]
    normalized = normalized[-MAX_HISTORY_MESSAGES:]
    messages = []

    for message in normalized:
        messages.append({
            "role": message["role"],
            "content": message["content"],
        })

    return messages


def sse_pack(payload):
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def build_user_prompt(question, file_context):
    return f"""
用户问题：
{question}

已选择的待分析文件上下文：
{file_context}

请基于以上文件上下文回答用户问题。
""".strip()


def build_selected_file_context(selected_results):
    if not isinstance(selected_results, list) or len(selected_results) == 0:
        return "用户本次没有选择任何分析结果文件。"

    sections = []
    total_chars = 0

    for index, file_info in enumerate(selected_results, start=1):
        section = build_single_file_context(index, file_info)
        total_chars = append_context_section(sections, section, total_chars)

        if total_chars >= MAX_CONTEXT_CHARS:
            break

    if total_chars >= MAX_CONTEXT_CHARS:
        sections.append("\n[文件上下文已达到长度上限，其余内容未继续传入。]")

    return "\n\n".join(sections)


def append_context_section(sections, section, total_chars):
    remaining_chars = MAX_CONTEXT_CHARS - total_chars

    if remaining_chars <= 0:
        return total_chars

    if len(section) > remaining_chars:
        section = section[:remaining_chars] + "\n[该文件上下文因长度限制已截断。]"

    sections.append(section)
    return total_chars + len(section)


def build_single_file_context(index, file_info):
    if not isinstance(file_info, dict):
        return f"## 文件 {index}\n前端传入的文件信息格式无效：{file_info}"

    display_name = file_info.get("name") or "未命名文件"
    display_type = file_info.get("type") or "unknown"
    raw_path = file_info.get("path") or file_info.get("name") or ""
    resolved_path = resolve_result_path(raw_path)

    if not resolved_path:
        return f"""## 文件 {index}：{display_name}
- 类型：{display_type}
- 前端路径：{raw_path}
- 状态：文件路径无效或不在 result 目录中，未传入文件内容。"""

    if not resolved_path.exists() or not resolved_path.is_file():
        return f"""## 文件 {index}：{display_name}
- 类型：{display_type}
- 前端路径：{raw_path}
- 状态：文件不存在，未传入文件内容。"""

    stat = resolved_path.stat()
    suffix = resolved_path.suffix.lower()
    supplemented_note = "\n- 选择状态：用户在当前对话中补充加入，请在后续回答中一并纳入分析。" if file_info.get("supplemented") else ""
    header = f"""## 文件 {index}：{display_name}
- 类型：{display_type}
- 路径：{resolved_path.relative_to(PROJECT_ROOT).as_posix()}
- 大小：{stat.st_size} bytes
- 修改时间：{datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")}{supplemented_note}"""

    if suffix in TABLE_EXTENSIONS:
        return f"{header}\n\n{read_table_context(resolved_path)}"


    return f"{header}\n\n文件说明：暂不支持解析该扩展名，当前只传入文件元信息。"


def resolve_result_path(raw_path):
    if not raw_path:
        return None

    candidate = Path(str(raw_path))
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate

    try:
        resolved = candidate.resolve()
        resolved.relative_to(RESULT_ROOT.resolve())
    except ValueError:
        return None

    return resolved


def read_text_context(file_path):
    content = file_path.read_text(encoding="utf-8", errors="replace")
    truncated = len(content) > MAX_TEXT_FILE_CHARS
    content = content[:MAX_TEXT_FILE_CHARS]
    suffix = "\n[该文本文件内容因长度限制已截断。]" if truncated else ""
    return f"文件内容：\n```text\n{content}\n```{suffix}"


def read_table_context(file_path):
    delimiter = "\t" if file_path.suffix.lower() == ".tsv" else ","
    rows = []

    with file_path.open("r", encoding="utf-8", errors="replace", newline="") as file:
        reader = csv.reader(file, delimiter=delimiter)

        for row_index, row in enumerate(reader):
            if row_index > MAX_TABLE_ROWS:
                break
            rows.append(row)

    if not rows:
        return "表格内容：文件为空。"

    header = rows[0]
    samples = rows[1:]
    table_payload = {
        "columns": header,
        "sample_rows": samples,
        "sample_row_count": len(samples),
    }

    return f"表格结构与样例数据：\n```json\n{json.dumps(table_payload, ensure_ascii=False, indent=2)}\n```"


# 接口1 deepseek api调用接口 /api/chat
@app.post("/api/chat")
def chat():
    payload = request.get_json(silent=True) or {}
    question = str(payload.get("question", "")).strip()
    model = payload.get("model") or "deepseek-v4-pro"
    selected_results = payload.get("selected_results") or []
    conversation_history = payload.get("conversation_history") or []

    if not question:
        return jsonify({"error": "question is required"}), 400

    if model not in AVAILABLE_MODELS:
        return jsonify({"error": "unsupported model"}), 400

    @stream_with_context
    def generate():
        try:
            response = client.chat.completions.create(
                model=model,
                messages=build_messages(question, selected_results, conversation_history),
                stream=True,
                reasoning_effort="high",
                extra_body={
                    "thinking": {"type": "enabled"}
                }
            )

            for chunk in response:
                if not chunk.choices:
                    continue

                choice = chunk.choices[0]
                delta = choice.delta
                reasoning_content = getattr(delta, "reasoning_content", None)
                content = getattr(delta, "content", None)

                if reasoning_content:
                    yield sse_pack({"type": "reasoning", "delta": reasoning_content})

                if content:
                    yield sse_pack({"type": "content", "delta": content})

            yield sse_pack({"type": "done"})
        except Exception as error:
            yield sse_pack({"type": "error", "message": str(error)})

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9090, debug=True)
