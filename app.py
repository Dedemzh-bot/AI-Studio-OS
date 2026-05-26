"""
AI Studio OS - Web GUI (Streamlit)
职责：为底层终端 Agent 管线提供可视化管理面板。
布局：三栏式 — 左栏导航+控制 | 中栏日志+输入 | 右栏文件目录
"""

import os
import sys
import json
import time
import subprocess
import threading
from datetime import datetime

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import streamlit as st

# ---- 路径常量 ----
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_DIR = os.path.join(ROOT_DIR, ".agent_workspace")
BEST_DIR = os.path.join(ROOT_DIR, "Knowledge", "best_practices")
ANTI_DIR = os.path.join(ROOT_DIR, "Knowledge", "anti_patterns")
META_FILE = os.path.join(WORKSPACE_DIR, "project_meta.json")
CONCEPT_FILE = os.path.join(WORKSPACE_DIR, "concept_brief.md")
STATUS_FILE = os.path.join(WORKSPACE_DIR, "task_status.json")

ICON_MAP = {".md": "📄", ".mmd": "📄", ".json": "📊", ".gd": "💻", ".py": "💻"}

# ---- 页面配置 ----
st.set_page_config(page_title="AI Studio OS", page_icon="🎮", layout="wide")

# ---- 自定义 CSS 匹配原型深色侧栏 ----
st.markdown("""
<style>
[data-testid="stSidebar"] {
    background-color: #2d333b;
}
[data-testid="stSidebar"] * {
    color: #fff !important;
}
[data-testid="stSidebar"] button[kind="secondary"] {
    background-color: #fff;
    color: #000 !important;
    text-align: left;
    border-radius: 0;
    margin-bottom: 2px;
}
</style>
""", unsafe_allow_html=True)

# ================================================================
# 工具函数
# ================================================================

def read_status() -> str:
    try:
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("current_state", "idle")
    except Exception:
        return "idle"


def sync_concept_to_file(text: str):
    try:
        os.makedirs(WORKSPACE_DIR, exist_ok=True)
        with open(CONCEPT_FILE, "w", encoding="utf-8") as f:
            f.write(text.strip())
    except Exception:
        pass


def open_file(filepath: str):
    abs_path = os.path.abspath(filepath)
    if sys.platform == "win32":
        os.startfile(abs_path)
    elif sys.platform == "darwin":
        subprocess.call(["open", abs_path])
    else:
        subprocess.call(["xdg-open", abs_path])


def get_file_icon(filename: str) -> str:
    ext = "." + filename.rsplit(".", 1)[-1] if "." in filename else ""
    return ICON_MAP.get(ext, "📁")


def scan_workspace_files() -> list:
    files = []
    if os.path.exists(WORKSPACE_DIR):
        for f in sorted(os.listdir(WORKSPACE_DIR)):
            fp = os.path.join(WORKSPACE_DIR, f)
            if os.path.isfile(fp) and not f.startswith("."):
                files.append(f)
    return files


def scan_knowledge(dir_path: str) -> list:
    if os.path.exists(dir_path):
        return sorted(os.listdir(dir_path))
    return []


def load_meta() -> dict:
    if os.path.exists(META_FILE):
        try:
            with open(META_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


# ================================================================
# Router 启动逻辑
# ================================================================

def start_router():
    if "log_lines" not in st.session_state:
        st.session_state["log_lines"] = ["[GUI] 正在启动 AI Studio OS 调度中枢..."]
    else:
        st.session_state["log_lines"].append("[GUI] 正在启动 AI Studio OS 调度中枢...")

    p = subprocess.Popen(
        [sys.executable, "-u", os.path.join(ROOT_DIR, "main_router.py")],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, errors="replace", cwd=ROOT_DIR,
    )

    st.session_state["router_proc"] = p

    def read_logs():
        try:
            for line in iter(p.stdout.readline, ""):
                if not line:
                    break
                st.session_state["log_lines"].append(line.strip())
                if len(st.session_state["log_lines"]) > 300:
                    st.session_state["log_lines"] = st.session_state["log_lines"][-200:]
        except Exception:
            pass

    thread = threading.Thread(target=read_logs, daemon=True)
    thread.start()


def stop_router():
    proc = st.session_state.get("router_proc")
    if proc and proc.poll() is None:
        try:
            proc.terminate()
            proc.wait(timeout=3)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass


# ================================================================
# 侧边栏导航
# ================================================================

with st.sidebar:
    st.markdown("### 🎮 AI Studio OS")
    page = st.radio("", ["📝 写案子", "📚 记忆积累"], label_visibility="collapsed")

    st.divider()

    # 启动 / 停止控制
    if st.button("🟢 启动研发", use_container_width=True):
        stop_router()
        start_router()

    current_state = read_status()
    state_colors = {
        "idle": "🟢", "pending_classification": "🟡", "clarifying_requirements": "🟣",
        "pending_design_approval": "🔵", "pending_plan_approval": "🔷",
        "pending_system_design": "🟦", "pending_system_approval": "🟩",
        "pending_schema_translate": "🟨", "pending_numerical": "🟧",
        "pending_numerical_approval": "🟥", "completed": "✅",
    }
    emoji = state_colors.get(current_state, "🟠")
    st.caption(f"{emoji} {current_state}")

    if st.button("⏹ 停止", use_container_width=True):
        stop_router()
        st.rerun()

    st.caption("启动 = 运行 main_router.py\n状态显示当前 Agent 阶段")


# ================================================================
# 写案子页面
# ================================================================

if page == "📝 写案子":
    col_left, col_right = st.columns([7, 3])

    with col_left:
        # ---- 终端日志 ----
        if "log_lines" not in st.session_state:
            st.session_state["log_lines"] = ["[GUI] 等待启动..."]
        log_text = "\n".join(st.session_state["log_lines"][-60:])
        st.text_area("终端日志", value=log_text, height=300, disabled=True,
                      key="log_display", label_visibility="collapsed")

        # ---- 需求输入 ----
        current_concept = ""
        if os.path.exists(CONCEPT_FILE):
            try:
                with open(CONCEPT_FILE, "r", encoding="utf-8") as f:
                    current_concept = f.read()
            except Exception:
                pass

        st.text_area(
            "需求输入（修改后 Ctrk+Enter 提交）",
            value=current_concept,
            height=120,
            key="concept_input",
            on_change=lambda: sync_concept_to_file(st.session_state.get("concept_input", "")),
            label_visibility="collapsed",
            placeholder="请输入文字...",
        )

    with col_right:
        st.caption("点击文件跳转目录打开")

        files = scan_workspace_files()
        if files:
            for f in files:
                fp = os.path.join(WORKSPACE_DIR, f)
                icon = get_file_icon(f)
                if st.button(f"{icon} {f}", key=f"ws_{f}", use_container_width=True):
                    open_file(fp)
        else:
            st.caption("（暂无下发文件）")


# ================================================================
# 记忆积累页面
# ================================================================

elif page == "📚 记忆积累":
    col_left, col_right = st.columns([7, 3])

    with col_left:
        st.subheader("知识库沉淀")
        doc_name = st.text_input("文档名字（在 .agent_workspace 内）", key="arch_doc",
                                  placeholder="例: system_design_draft.md")
        meta_comment = st.text_area("老板批注 (Meta-Comment)", key="arch_comment",
                                     placeholder="例: 本案状态机流转极其严谨")

        btn1, btn2 = st.columns(2)
        list_type = None
        with btn1:
            if st.button("🔴 归入黑榜 (反面教训)", use_container_width=True):
                list_type = "black"
        with btn2:
            if st.button("🟢 归入红榜 (优秀范式)", use_container_width=True):
                list_type = "red"

        if list_type and doc_name.strip():
            arch_cmd = [
                sys.executable,
                os.path.join(ROOT_DIR, "Agents", "archivist_agent.py"),
                doc_name.strip(), "all", list_type,
                meta_comment.strip() or "（无评语）",
            ]
            with st.spinner("正在归档..."):
                try:
                    result = subprocess.run(arch_cmd, capture_output=True, text=True, cwd=ROOT_DIR)
                    if result.returncode == 0:
                        st.success("归档成功！")
                    else:
                        st.error(f"失败: {result.stderr[-300:]}")
                except Exception as e:
                    st.error(f"异常: {e}")

    with col_right:
        st.subheader("🟢 优秀范式 (红榜)")
        best_files = scan_knowledge(BEST_DIR)
        if best_files:
            for f in best_files:
                fp = os.path.join(BEST_DIR, f)
                if st.button(f"📄 {f}", key=f"best_{f}", use_container_width=True):
                    open_file(fp)
        else:
            st.caption("（空）")

        st.divider()

        st.subheader("🔴 反面教训 (黑榜)")
        anti_files = scan_knowledge(ANTI_DIR)
        if anti_files:
            for f in anti_files:
                fp = os.path.join(ANTI_DIR, f)
                if st.button(f"📄 {f}", key=f"anti_{f}", use_container_width=True):
                    open_file(fp)
        else:
            st.caption("（空）")

# ---- 自动刷新 ----
proc = st.session_state.get("router_proc")
if proc and proc.poll() is None:
    time.sleep(2)
    st.rerun()
