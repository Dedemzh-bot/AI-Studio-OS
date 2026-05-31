"""
ConfigTable Bridge Server — 配表工具桥接服务
监听 localhost:8081，接收 AI Studio OS 的配表请求
独立运行在 ConfigTable/ 目录下，隔离于主项目
"""

import json
import os
import sys
import subprocess
import time
from datetime import datetime

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(ROOT_DIR)
EXCEL_DIR = os.path.join(PROJECT_ROOT, "Excel")
GAMEDATA_DIR = os.path.join(ROOT_DIR, "knowledge", "gamedata")
SESSION_FILE = os.path.join(ROOT_DIR, ".session_state.json")
MODIFIED_FILE = os.path.join(ROOT_DIR, ".modified_files.json")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

session_log = []
modified_files = set()
active_task = False


def load_session():
    global session_log, modified_files, active_task
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
            session_log = d.get("log", [])
            modified_files = set(d.get("modified", []))
            active_task = d.get("active", False)
        except Exception:
            pass


def save_session():
    try:
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "log": session_log[-200:],
                "modified": sorted(modified_files),
                "active": active_task,
            }, f, ensure_ascii=False)
    except Exception:
        pass


load_session()


@app.get("/status")
def api_status():
    return JSONResponse({"active": active_task, "log": session_log[-80:]})


@app.get("/files")
def api_files():
    """返回 Excel/ 下所有 JSON 文件"""
    files = []
    if os.path.exists(EXCEL_DIR):
        for f in sorted(os.listdir(EXCEL_DIR)):
            fp = os.path.join(EXCEL_DIR, f)
            if os.path.isfile(fp) and f.endswith(".json"):
                files.append({
                    "name": f,
                    "size": os.path.getsize(fp),
                    "mtime": os.path.getmtime(fp),
                })
    files.sort(key=lambda x: x["name"])
    return JSONResponse({"files": files, "modified": sorted(modified_files)})


@app.post("/open_file")
async def api_open_file(data: dict):
    fname = data.get("file", "")
    fp = os.path.join(EXCEL_DIR, fname)
    if os.path.exists(fp):
        abs_path = os.path.abspath(fp)
        if sys.platform == "win32":
            os.startfile(abs_path)
        elif sys.platform == "darwin":
            subprocess.call(["open", abs_path])
        else:
            subprocess.call(["xdg-open", abs_path])
    return JSONResponse({"ok": True})


@app.post("/design")
async def api_design(data: dict):
    """启动配表设计任务（由 AI Studio OS 转发）"""
    global active_task, session_log
    text = data.get("text", "").strip()
    if not text:
        return JSONResponse({"ok": False, "error": "需求文本为空"})

    active_task = True
    timestamp = datetime.now().strftime("%H:%M:%S")
    session_log.append(f"[{timestamp}] 收到配表需求: {text[:100]}")
    save_session()

    # 模拟配表执行（后续接入真实 Agent 管线）
    try:
        # 记录本次会话前已有的文件
        before = set()
        if os.path.exists(EXCEL_DIR):
            before = {f for f in os.listdir(EXCEL_DIR) if f.endswith(".json")}

        session_log.append(f"[{timestamp}] 配表任务执行中...")
        save_session()

        # TODO: 接入 ConfigTable 的 Agent 管线
        # subprocess.run([sys.executable, "references/scripts/...", text], ...)

        time.sleep(1)  # 模拟执行

        # 检测新增/修改的文件
        after = set()
        if os.path.exists(EXCEL_DIR):
            after = {f for f in os.listdir(EXCEL_DIR) if f.endswith(".json")}
        new_or_changed = after - before
        modified_files.update(new_or_changed)

        session_log.append(f"[{timestamp}] 配表完成，受影响文件: {sorted(new_or_changed)}")
        active_task = False
        save_session()

        return JSONResponse({
            "ok": True,
            "log": session_log[-80:],
            "modified": sorted(modified_files),
        })
    except Exception as e:
        session_log.append(f"[{timestamp}] 配表失败: {e}")
        active_task = False
        save_session()
        return JSONResponse({"ok": False, "error": str(e)})


@app.post("/quick")
async def api_quick(data: dict):
    """快速修改配置"""
    global session_log
    text = data.get("text", "").strip()
    if not text:
        return JSONResponse({"ok": False, "error": "需求文本为空"})

    timestamp = datetime.now().strftime("%H:%M:%S")
    session_log.append(f"[{timestamp}] 快速修改: {text[:100]}")

    # 模拟执行
    time.sleep(0.5)
    session_log.append(f"[{timestamp}] 修改完成")
    save_session()
    return JSONResponse({"ok": True, "log": session_log[-80:]})


@app.post("/cancel")
def api_cancel():
    global active_task
    active_task = False
    session_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 任务已取消")
    save_session()
    return JSONResponse({"ok": True})


@app.post("/clear_session")
def api_clear_session():
    global session_log, modified_files
    session_log = []
    modified_files = set()
    save_session()
    return JSONResponse({"ok": True})


if __name__ == "__main__":
    import uvicorn
    print(f"ConfigTable Bridge Server -> http://localhost:8081")
    uvicorn.run(app, host="127.0.0.1", port=8081, log_level="warning")
