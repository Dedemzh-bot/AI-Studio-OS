"""
AI Studio OS - FastAPI Backend
WebSocket + REST API hybrid architecture
"""

import json
import os
import sys
import shutil
import subprocess
import time
import asyncio
import threading
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, 'frozen', False):
    BUNDLE_DIR = sys._MEIPASS
    DATA_DIR = os.path.dirname(sys.executable)
    src_kb = os.path.join(BUNDLE_DIR, "Knowledge")
    dst_kb = os.path.join(DATA_DIR, "Knowledge")
    if os.path.isdir(src_kb) and not os.path.exists(dst_kb):
        shutil.copytree(src_kb, dst_kb)
else:
    BUNDLE_DIR = ROOT_DIR
    DATA_DIR = ROOT_DIR

WS_DIR = os.path.join(DATA_DIR, ".agent_workspace")
KNOWLEDGE_DIR = os.path.join(DATA_DIR, "Knowledge")
BEST_DIR = os.path.join(KNOWLEDGE_DIR, "best_practices")
ANTI_DIR = os.path.join(KNOWLEDGE_DIR, "anti_patterns")
STATUS_FILE = os.path.join(WS_DIR, "task_status.json")
CONCEPT_FILE = os.path.join(WS_DIR, "concept_brief.md")
PROMPT_FILE = os.path.join(WS_DIR, ".web_prompt.json")
RESPONSE_FILE = os.path.join(WS_DIR, ".web_response.json")
LOG_FILE = os.path.join(WS_DIR, ".web_log.jsonl")

FRAMEWORK_FILES = {
    "blueprint.json", "active_schema.json", "current_result.json",
    "task_status.json", "review_board.md", "task_route.json",
    "boss_feedback.txt", "project_meta.json", "concept_brief.md",
}

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

router_proc = None
engine_start_ts = 0
active_ws: WebSocket | None = None


# ==================== REST API ====================

@app.get("/api/status")
def api_status():
    try:
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            state = json.load(f).get("current_state", "idle")
    except Exception:
        state = "idle"
    return JSONResponse({"state": state})


@app.get("/api/files")
def api_files():
    if not os.path.exists(WS_DIR):
        return JSONResponse({"files": []})

    files = []
    for f in os.listdir(WS_DIR):
        fp = os.path.join(WS_DIR, f)
        # 只取直接文件，排除子目录（如 project_db/）
        if not os.path.isfile(fp) or f.startswith("."):
            continue
        if f in FRAMEWORK_FILES:
            continue
        mtime = os.path.getmtime(fp)
        if mtime < engine_start_ts:
            continue
        if os.path.getsize(fp) < 10:
            continue
        files.append({
            "name": f,
            "path": f".agent_workspace/{f}",
            "mtime": mtime,
            "size": os.path.getsize(fp),
        })
    files.sort(key=lambda x: x["mtime"])
    return JSONResponse({"files": files})


@app.post("/api/open_file")
async def api_open_file(data: dict):
    fp = os.path.join(WS_DIR, data.get("file", ""))
    if os.path.exists(fp):
        abs_path = os.path.abspath(fp)
        if sys.platform == "win32":
            os.startfile(abs_path)
        elif sys.platform == "darwin":
            subprocess.call(["open", abs_path])
        else:
            subprocess.call(["xdg-open", abs_path])
    return JSONResponse({"ok": True})


@app.post("/api/open_knowledge")
async def api_open_knowledge(data: dict):
    d = BEST_DIR if data.get("type") == "best" else ANTI_DIR
    fp = os.path.join(d, data.get("file", ""))
    if os.path.exists(fp):
        abs_path = os.path.abspath(fp)
        if sys.platform == "win32":
            os.startfile(abs_path)
        elif sys.platform == "darwin":
            subprocess.call(["open", abs_path])
        else:
            subprocess.call(["xdg-open", abs_path])
    return JSONResponse({"ok": True})


@app.post("/api/concept")
async def api_concept(data: dict):
    text = data.get("text", "")
    if text.strip():
        os.makedirs(WS_DIR, exist_ok=True)
        with open(CONCEPT_FILE, "w", encoding="utf-8") as f:
            f.write(text.strip())
    return JSONResponse({"ok": True})


@app.get("/api/knowledge")
def api_knowledge(type: str = "best"):
    d = BEST_DIR if type == "best" else ANTI_DIR
    files = sorted(os.listdir(d)) if os.path.exists(d) else []
    return JSONResponse({"files": files})


@app.post("/api/archive")
async def api_archive(data: dict):
    python_exe = shutil.which("python") or "python" if getattr(sys, 'frozen', False) else sys.executable
    cmd = [python_exe,
           os.path.join(BUNDLE_DIR, "Agents", "archivist_agent.py"),
           data.get("doc", ""), "all", data.get("type", "red"),
           data.get("comment", "") or "（无评语）"]
    try:
        env = os.environ.copy()
        env["AI_STUDIO_DATA_DIR"] = DATA_DIR
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=BUNDLE_DIR, env=env)
        return JSONResponse({"ok": r.returncode == 0, "error": r.stderr[-300:] if r.returncode else ""})
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)})


# ==================== WebSocket ====================

def get_prompt_data():
    if not os.path.exists(PROMPT_FILE):
        return None
    try:
        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
        if d.get("answered"):
            return None
        return d.get("prompt", "")
    except Exception:
        return None


def submit_answer(ans: str):
    try:
        os.makedirs(WS_DIR, exist_ok=True)
        with open(RESPONSE_FILE, "w", encoding="utf-8") as f:
            json.dump({"answer": ans, "ts": time.time()}, f)
    except Exception:
        pass


@app.websocket("/ws/terminal")
async def ws_terminal(websocket: WebSocket):
    global router_proc, engine_start_ts, active_ws

    await websocket.accept()

    if active_ws is not None:
        await websocket.send_json({"type": "error", "msg": "控制台已在另一个窗口运行中"})
        await websocket.close()
        return

    active_ws = websocket
    engine_start_ts = time.time()

    # Clear old communication state
    CACHE_FILE = os.path.join(WS_DIR, ".concept_brief_cache.txt")
    for f in [PROMPT_FILE, RESPONSE_FILE, CACHE_FILE]:
        if os.path.exists(f):
            os.remove(f)
    os.makedirs(WS_DIR, exist_ok=True)
    open(LOG_FILE, "w", encoding="utf-8").close()

    env = os.environ.copy()
    env["AI_STUDIO_WEB_MODE"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["AI_STUDIO_DATA_DIR"] = DATA_DIR

    try:
        if getattr(sys, 'frozen', False):
            python_cmd = shutil.which("python") or "python"
        else:
            python_cmd = sys.executable
        router_proc = subprocess.Popen(
            [python_cmd, "-u", os.path.join(BUNDLE_DIR, "main_router.py")],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            cwd=BUNDLE_DIR, env=env,
            bufsize=1, encoding="utf-8", errors="replace",
        )
    except Exception as e:
        await websocket.send_json({"type": "error", "msg": f"引擎启动失败: {e}"})
        active_ws = None
        return

    # Immediately push startup confirmation
    ws_queue = asyncio.Queue()
    await ws_queue.put({"type": "log", "text": f"[GUI] 引擎已启动 (PID: {router_proc.pid})"})
    stop_flag = threading.Event()
    loop = asyncio.get_running_loop()

    # Thread: read Router stdout (strip ANSI codes)
    def stdout_reader():
        import re
        ansi_re = re.compile(r'\x1b\[[0-9;]*m')
        try:
            for line in iter(router_proc.stdout.readline, ""):
                if stop_flag.is_set():
                    break
                if line and line.strip():
                    clean = ansi_re.sub("", line.strip())
                    loop.call_soon_threadsafe(ws_queue.put_nowait, {"type": "log", "text": clean})
        except Exception:
            pass

    # Thread: poll HITL prompts  
    def hitl_poller():
        last_prompt = ""
        while not stop_flag.is_set():
            prompt = get_prompt_data()
            if prompt and prompt != last_prompt:
                last_prompt = prompt
                loop.call_soon_threadsafe(ws_queue.put_nowait, {"type": "hitl_req", "msg": prompt})
            elif not prompt:
                last_prompt = ""
            time.sleep(1)

    t1 = threading.Thread(target=stdout_reader, daemon=True)
    t2 = threading.Thread(target=hitl_poller, daemon=True)
    t1.start()
    t2.start()

    async def consumer():
        while True:
            msg = await ws_queue.get()
            if msg["type"] == "log":
                try:
                    await websocket.send_text(msg["text"])
                except Exception:
                    break
            elif msg["type"] == "hitl_req":
                try:
                    await websocket.send_json(msg)
                except Exception:
                    break
            elif msg["type"] == "engine_dead":
                try:
                    await websocket.send_json({"type": "engine_exit", "msg": msg.get("text", "引擎已退出")})
                except Exception:
                    pass
                break

    async def receiver():
        try:
            while True:
                data = await websocket.receive_text()
                submit_answer(data)
        except WebSocketDisconnect:
            stop_flag.set()
            ws_queue.put_nowait({"type": "engine_dead", "text": ""})

    async def engine_monitor():
        while not stop_flag.is_set() and router_proc.poll() is None:
            await asyncio.sleep(1)
        if stop_flag.is_set():
            return
        await asyncio.sleep(0.5)
        loop.call_soon_threadsafe(ws_queue.put_nowait, {"type": "engine_dead", "text": "[System] 引擎进程已退出"})

    try:
        await asyncio.gather(consumer(), receiver(), engine_monitor())
    except WebSocketDisconnect:
        stop_flag.set()
        if not ws_queue.full():
            ws_queue.put_nowait({"type": "engine_dead", "text": ""})
    finally:
        stop_flag.set()
        active_ws = None
        if router_proc and router_proc.poll() is None:
            router_proc.terminate()
            try:
                router_proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                router_proc.kill()


# ==================== Static Files ====================

@app.get("/")
async def root():
    return FileResponse(os.path.join(BUNDLE_DIR, "index.html"))


# ==================== Startup ====================

if __name__ == "__main__":
    import uvicorn
    import webbrowser
    import socket
    import threading as _threading

    PORT = 8080
    URL = f"http://localhost:{PORT}"

    # 端口检测
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.settimeout(1)
        s.connect(("127.0.0.1", PORT))
        print(f"AI Studio OS — port {PORT} 已被占用，可能已在运行。")
        webbrowser.open(URL)
        input("按 Enter 退出...")
        sys.exit(0)
    except (socket.timeout, ConnectionRefusedError, OSError):
        pass
    finally:
        s.close()

    print(f"AI Studio OS v2 (FastAPI + WebSocket)")
    print(f"Starting server -> {URL}")

    def _open_browser():
        import time as _time
        _time.sleep(1.5)
        webbrowser.open(URL)

    _threading.Thread(target=_open_browser, daemon=True).start()

    try:
        uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="warning")
    except KeyboardInterrupt:
        print("\nServer stopped.")
