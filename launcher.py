"""AI Studio OS - One-click Launcher (FastAPI edition)"""
import os, sys, subprocess, time, webbrowser, socket

if getattr(sys, 'frozen', False):
    ROOT_DIR = os.path.dirname(sys.executable)
else:
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

PORT = 8080
URL = f"http://localhost:{PORT}"
SERVER_SCRIPT = os.path.join(ROOT_DIR, "server.py")

if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding="utf-8")
    except: pass

def port_in_use():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.settimeout(1)
        s.connect(("127.0.0.1", PORT)); s.close(); return True
    except: return False

def main():
    print("AI Studio OS v2 (FastAPI + WebSocket)")
    if not os.path.exists(SERVER_SCRIPT):
        print("ERROR: server.py not found!"); input("Press Enter to exit..."); return

    if port_in_use():
        print(f"Server already on port {PORT}. Opening browser...")
        os.startfile(URL) if sys.platform == "win32" else webbrowser.open(URL)
        input("Press Enter to exit (server stays running)..."); return

    # 用当前 Python 环境（确保安装了 fastapi/uvicorn）
    python_exe = sys.executable

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.Popen(
        [python_exe, "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", str(PORT), "--log-level", "warning"],
        cwd=ROOT_DIR, env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )
    print("Starting server...")

    for _ in range(20):
        time.sleep(0.5)
        if port_in_use():
            print("Server ready!")
            os.startfile(URL) if sys.platform == "win32" else webbrowser.open(URL)
            print(f"Browser -> {URL}")
            print("Close this window or press Enter to stop.")
            try: input()
            except: pass
            print("Stopping..."); proc.terminate()
            try: proc.wait(timeout=5)
            except: proc.kill()
            print("Server stopped."); return

    print("ERROR: Server failed to start. Checking logs...")
    proc.terminate()
    try: proc.wait(timeout=3)
    except: proc.kill()
    time.sleep(1)
    if proc.stderr:
        err = proc.stderr.read().decode("utf-8", errors="replace")
        if err:
            print(f"Server error log:\n{err.strip()}")
    input("Press Enter to exit...")

if __name__ == "__main__": main()
