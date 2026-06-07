"""
Legacy compatibility entrypoint.

AI Studio OS now has one supported web entrypoint: server.py.
Running ``python app.py`` remains supported and delegates to it.
"""

import runpy
from pathlib import Path


if __name__ == "__main__":
    server_path = Path(__file__).with_name("server.py")
    print("[AI Studio OS] app.py 已合并到 server.py，正在启动统一 Web 服务...")
    runpy.run_path(str(server_path), run_name="__main__")
