"""
AI Studio OS - HTTP Backend
python server.py → http://localhost:8080
"""

import json
import os
import sys
import subprocess
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_DIR = os.path.join(ROOT_DIR, ".agent_workspace")
STATUS_FILE = os.path.join(WORKSPACE_DIR, "task_status.json")
CONCEPT_FILE = os.path.join(WORKSPACE_DIR, "concept_brief.md")
BEST_DIR = os.path.join(ROOT_DIR, "Knowledge", "best_practices")
ANTI_DIR = os.path.join(ROOT_DIR, "Knowledge", "anti_patterns")
LOG_FILE = os.path.join(WORKSPACE_DIR, ".web_log.jsonl")
PROMPT_FILE = os.path.join(WORKSPACE_DIR, ".web_prompt.json")

router_proc = None
log_buffer = ["[Server] Backend started, waiting for engine..."]


# ==================== Backend Functions ====================

def read_status():
    try:
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("current_state", "idle")
    except Exception:
        return "idle"


def sync_concept(text):
    try:
        os.makedirs(WORKSPACE_DIR, exist_ok=True)
        with open(CONCEPT_FILE, "w", encoding="utf-8") as f:
            f.write(text.strip())
    except Exception:
        pass


def open_file(filename):
    fp = os.path.join(WORKSPACE_DIR, filename)
    if not os.path.exists(fp):
        return
    abs_path = os.path.abspath(fp)
    if sys.platform == "win32":
        os.startfile(abs_path)
    elif sys.platform == "darwin":
        subprocess.call(["open", abs_path])
    else:
        subprocess.call(["xdg-open", abs_path])


def scan_workspace_files():
    files = []
    if os.path.exists(WORKSPACE_DIR):
        for f in sorted(os.listdir(WORKSPACE_DIR)):
            fp = os.path.join(WORKSPACE_DIR, f)
            if os.path.isfile(fp) and not f.startswith("."):
                files.append(f)
    return files


def scan_dir(path):
    if os.path.exists(path):
        return sorted([f for f in os.listdir(path) if not f.startswith("_")])
    return []


def get_web_logs():
    if not os.path.exists(LOG_FILE):
        return log_buffer[-80:]
    lines = []
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    lines.append(line)
    except Exception:
        pass
    return lines[-80:]


def get_prompt():
    if not os.path.exists(PROMPT_FILE):
        return {"active": False}
    try:
        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {"active": False}
    if data.get("answered"):
        return {"active": False}
    return {"active": True, "prompt": data.get("prompt", ""), "ts": data.get("ts", 0)}


def answer_prompt(answer):
    resp_file = os.path.join(WORKSPACE_DIR, ".web_response.json")
    try:
        os.makedirs(WORKSPACE_DIR, exist_ok=True)
        with open(resp_file, "w", encoding="utf-8") as f:
            json.dump({"answer": answer, "ts": time.time()}, f)
    except Exception:
        pass


def start_router():
    global router_proc
    if router_proc and router_proc.poll() is None:
        return
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
    if os.path.exists(PROMPT_FILE):
        os.remove(PROMPT_FILE)
    resp = os.path.join(WORKSPACE_DIR, ".web_response.json")
    if os.path.exists(resp):
        os.remove(resp)

    env = os.environ.copy()
    env["AI_STUDIO_WEB_MODE"] = "1"
    router_proc = subprocess.Popen(
        [sys.executable, "-u", os.path.join(ROOT_DIR, "main_router.py")],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, cwd=ROOT_DIR, env=env,
    )
    import threading
    def read():
        try:
            for line in iter(router_proc.stdout.readline, ""):
                if line:
                    log_buffer.append(line.strip())
                    if len(log_buffer) > 500:
                        log_buffer[:] = log_buffer[-200:]
        except Exception:
            pass
    threading.Thread(target=read, daemon=True).start()


def stop_router():
    global router_proc
    if router_proc and router_proc.poll() is None:
        try:
            router_proc.terminate()
            router_proc.wait(timeout=3)
        except Exception:
            try:
                router_proc.kill()
            except Exception:
                pass


def run_archivist(doc, list_type, comment):
    cmd = [sys.executable,
           os.path.join(ROOT_DIR, "Agents", "archivist_agent.py"),
           doc, "all", list_type, comment]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT_DIR)
        return {"ok": result.returncode == 0, "error": result.stderr[-300:] if result.returncode else ""}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ==================== HTTP Handler ====================

class APIHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT_DIR, **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        if path == "/api/status":
            return self._json({"state": read_status()})
        elif path == "/api/logs":
            return self._json({"lines": get_web_logs()})
        elif path == "/api/prompt":
            return self._json(get_prompt())
        elif path == "/api/files":
            return self._json({"files": scan_workspace_files()})
        elif path == "/api/knowledge":
            ktype = params.get("type", ["best"])[0]
            d = BEST_DIR if ktype == "best" else ANTI_DIR
            return self._json({"files": scan_dir(d)})
        return super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path
        cl = int(self.headers.get("Content-Length", 0))
        try:
            data = json.loads(self.rfile.read(cl)) if cl else {}
        except Exception:
            data = {}

        if path == "/api/start":
            start_router()
            return self._json({"ok": True})
        elif path == "/api/stop":
            stop_router()
            return self._json({"ok": True})
        elif path == "/api/respond":
            answer_prompt(data.get("answer", ""))
            return self._json({"ok": True})
        elif path == "/api/concept":
            sync_concept(data.get("text", ""))
            return self._json({"ok": True})
        elif path == "/api/open":
            open_file(data.get("file", ""))
            return self._json({"ok": True})
        elif path == "/api/open_knowledge":
            d = BEST_DIR if data.get("type") == "best" else ANTI_DIR
            fp = os.path.join(d, data.get("file", ""))
            if os.path.exists(fp):
                open_file(fp)
            return self._json({"ok": True})
        elif path == "/api/archive":
            r = run_archivist(data.get("doc", ""), data.get("type", "red"), data.get("comment", ""))
            return self._json({"ok": r["ok"], "error": r.get("error", "")})
        return self._json({"error": "unknown endpoint"}, 404)

    def _json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def log_message(self, format, *args):
        pass


# ==================== Start ====================

if __name__ == "__main__":
    port = 8080
    server = HTTPServer(("0.0.0.0", port), APIHandler)
    print(f"AI Studio OS HTTP Server -> http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        stop_router()
        server.server_close()
        print("\nServer stopped.")
