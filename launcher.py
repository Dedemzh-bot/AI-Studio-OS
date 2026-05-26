"""
AI Studio OS - One-click Launcher (single instance)
"""

import os
import sys
import subprocess
import time
import webbrowser
import socket

# ---- Path ----
if getattr(sys, 'frozen', False):
    ROOT_DIR = os.path.dirname(sys.executable)
else:
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

SERVER_SCRIPT = os.path.join(ROOT_DIR, "server.py")
URL = "http://localhost:8080"
PORT = 8080

# ---- Encode ----
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def port_in_use(port: int) -> bool:
    """Check if the port is already listening."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            s.connect(("127.0.0.1", port))
            return True
    except Exception:
        return False


def main():
    print("AI Studio OS v2")
    print(f"Root dir: {ROOT_DIR}")
    print(f"Server script: {SERVER_SCRIPT}")

    if not os.path.exists(SERVER_SCRIPT):
        print("ERROR: server.py not found!")
        print("Make sure AI_Studio_OS.exe is in the project root directory.")
        input("Press Enter to exit...")
        return

    # Check if already running
    if port_in_use(PORT):
        print(f"Server already running on port {PORT}. Opening browser...")
        webbrowser.open(URL)
        input("Press Enter to close this window (server stays running)...")
        return

    # Start server subprocess
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    # Use 'python' from PATH, not sys.executable (which is the EXE itself)
    python_exe = "python"
    # Fallback: if py launcher is available, use it
    try:
        subprocess.run(["py", "-3", "--version"], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0, timeout=3)
        python_exe = "py"
    except Exception:
        pass

    try:
        proc = subprocess.Popen(
            [python_exe, "-u", SERVER_SCRIPT],
            cwd=ROOT_DIR,
            env=env,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
    except Exception as e:
        print(f"ERROR starting server: {e}")
        input("Press Enter to exit...")
        return

    print("Waiting for server to be ready...")
    for _ in range(20):
        time.sleep(0.5)
        if port_in_use(PORT):
            print("Server ready!")
            webbrowser.open(URL)
            print(f"Browser -> {URL}")
            print("Close this window or press Enter to stop the server.")
            try:
                input()
            except (EOFError, KeyboardInterrupt):
                pass
            print("Stopping...")
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
            print("Server stopped.")
            return

    # Server never started - capture output
    print("ERROR: Server failed to start after 10 seconds.")
    print("Possible causes: Python not in PATH, port conflict, or import error.")
    # Try to get server output
    try:
        proc.terminate()
        out, _ = proc.communicate(timeout=3)
        if out:
            print("--- Server output ---")
            print(out[-500:])
    except Exception:
        proc.kill()
    input("Press Enter to exit...")


if __name__ == "__main__":
    main()
