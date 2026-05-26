"""
Web I/O Bridge — 终端与 Web GUI 的通信桥梁。
当 WEB_MODE=1 时，input() 和 print() 透传到此模块，实现终端 ↔ Web 双向交互。
"""

import json
import os
import sys
import time

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.join(ROOT_DIR, ".agent_workspace")
PROMPT_FILE = os.path.join(WORKSPACE, ".web_prompt.json")
RESPONSE_FILE = os.path.join(WORKSPACE, ".web_response.json")
LOG_FILE = os.path.join(WORKSPACE, ".web_log.jsonl")

_web_mode = os.environ.get("AI_STUDIO_WEB_MODE") == "1"

# ANSI strip regex
import re
_ansi_re = re.compile(r'\x1b\[[0-9;]*m')


def is_web_mode() -> bool:
    return _web_mode


def web_print(*args, **kwargs):
    """Web 模式下的 print：写入日志文件 + 原 print"""
    msg = " ".join(str(a) for a in args)
    clean = _ansi_re.sub("", msg)
    _append_log(clean)
    # 始终也输出到终端
    print(*args, **kwargs)


def web_input(prompt: str = "") -> str:
    """Web 模式下的 input：写提示到文件，轮询等待响应"""
    if prompt:
        web_print(prompt)
    if not _web_mode:
        return input()

    _write_prompt(prompt)
    # 轮询等待响应
    while True:
        response = _read_response()
        if response is not None:
            web_print(f">>> {response}")
            return response
        time.sleep(0.5)


def get_pending_prompt() -> dict | None:
    """供 server.py 查询：是否有待处理的 HITL 提示"""
    if not os.path.exists(PROMPT_FILE):
        return None
    try:
        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if data.get("answered"):
            return None
        return data
    except Exception:
        return None


def answer_prompt(answer: str):
    """供 server.py 调用：提交用户回答"""
    try:
        os.makedirs(WORKSPACE, exist_ok=True)
        with open(RESPONSE_FILE, "w", encoding="utf-8") as f:
            json.dump({"answer": answer, "ts": time.time()}, f)
    except Exception:
        pass


def get_recent_logs(n: int = 80) -> list[str]:
    """获取最近 n 条日志"""
    if not os.path.exists(LOG_FILE):
        return []
    lines = []
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    lines.append(line)
    except Exception:
        pass
    return lines[-n:]


# ---- 内部 ----

def _append_log(msg: str):
    try:
        os.makedirs(WORKSPACE, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass


def _write_prompt(prompt: str):
    try:
        os.makedirs(WORKSPACE, exist_ok=True)
        # 清除旧响应
        if os.path.exists(RESPONSE_FILE):
            os.remove(RESPONSE_FILE)
        with open(PROMPT_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "prompt": prompt.strip(),
                "ts": time.time(),
                "answered": False,
            }, f, ensure_ascii=False)
    except Exception:
        pass


def _read_response() -> str | None:
    if not os.path.exists(RESPONSE_FILE):
        return None
    try:
        with open(RESPONSE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # 标记提示已答
        if os.path.exists(PROMPT_FILE):
            with open(PROMPT_FILE, "r", encoding="utf-8") as f:
                pd = json.load(f)
            pd["answered"] = True
            with open(PROMPT_FILE, "w", encoding="utf-8") as f:
                json.dump(pd, f, ensure_ascii=False)
        os.remove(RESPONSE_FILE)
        return data.get("answer", "")
    except Exception:
        return None
