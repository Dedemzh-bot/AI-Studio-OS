"""
AI Studio OS - Web GUI (Streamlit)
职责：为底层终端 Agent 管线提供可视化管理面板。
严格在本地运行，不修改 main_router.py 等后端逻辑。
"""

import os
import sys
import json
import time
import subprocess
import threading
from datetime import datetime

# ---- 强制 UTF-8 for Windows ----
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

# ---- 文件映射 ----
FILE_LABELS = {
    "concept_brief.md": "概念简案",
    "system_design_draft.md": "主策宏观草案",
    "system_design_detail.md": "系统策划详细案",
    "system_schema.json": "系统 Schema",
    "system_numerical_data.json": "数值配置表",
    "system_numerical_docs.json": "数值字典",
    "system_flow.mmd": "系统流程图",
    "tech_blueprint.md": "程序开发蓝图",
    "task_plan.md": "PM 任务拆解",
    "task_route.json": "路由指令",
    "audit_feedback.json": "审查反馈",
    "ui_config.json": "UI 表现配置",
    "generated_skill.gd": "生成代码",
    "review_board.md": "验收表",
    "project_meta.json": "项目元数据",
    "current_result.json": "当前产出",
    "active_schema.json": "当前契约",
}

# ---- 页面配置 ----
st.set_page_config(page_title="AI Studio OS", page_icon="🎮", layout="wide")

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
    """用系统默认程序打开文件"""
    abs_path = os.path.abspath(filepath)
    if sys.platform == "win32":
        os.startfile(abs_path)
    elif sys.platform == "darwin":
        subprocess.call(["open", abs_path])
    else:
        subprocess.call(["xdg-open", abs_path])


def build_display_name(filename: str, meta: dict) -> str:
    """
    基于 Meta 数据构建动态展示名。
    格式: 📜 {中文标签}_{tag}_{system_name}_{version}.{ext}
    无 meta 时回退为原始文件名+标签。
    """
    label = FILE_LABELS.get(filename, filename.rsplit(".", 1)[0])
    ext = filename.rsplit(".", 1)[-1] if "." in filename else ""

    sys_name = meta.get("system_name", "")
    tag = meta.get("primary_tag", "")
    ver = meta.get("version", "")

    if sys_name:
        parts = [label]
        if tag and tag != "通用":
            parts.append(tag)
        parts.append(sys_name)
        if ver:
            parts.append(ver)
        return f"\U0001f4dc {'_'.join(parts)}.{ext}"
    else:
        return f"\U0001f4dc {label}.{ext}"


def scan_workspace_files() -> list:
    """扫描 workspace 返回文件列表"""
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
# 主 Router 启动逻辑
# ================================================================

def start_router(log_placeholder):
    """非阻塞启动 main_router.py，实时推送日志到 UI"""
    log_placeholder.markdown("```\n[GUI] 正在启动 AI Studio OS 调度中枢...\n```")

    p = subprocess.Popen(
        [sys.executable, "-u", os.path.join(ROOT_DIR, "main_router.py")],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, errors="replace", cwd=ROOT_DIR,
    )

    log_lines = []
    st.session_state["router_pid"] = p.pid

    def read_logs():
        try:
            for line in iter(p.stdout.readline, ""):
                if not line:
                    break
                log_lines.append(line.strip())
                if len(log_lines) > 200:
                    log_lines.pop(0)
                log_placeholder.markdown("```\n" + "\n".join(log_lines[-60:]) + "\n```")
        except Exception:
            pass

    thread = threading.Thread(target=read_logs, daemon=True)
    thread.start()
    st.session_state["log_thread"] = thread


def stop_router():
    pid = st.session_state.get("router_pid")
    if pid:
        try:
            import signal
            os.kill(pid, signal.SIGTERM)
        except Exception:
            pass
        st.session_state.pop("router_pid", None)


# ================================================================
# 侧边栏
# ================================================================

st.sidebar.title("🎮 AI Studio OS")
page = st.sidebar.radio("导航", ["写案子", "档案管理"])

# ================================================================
# 写案子页面
# ================================================================

if page == "写案子":
    col_center, col_right = st.columns([6, 3])

    with col_center:
        st.header("控制台")

        # ---- 终端日志区 ----
        log_placeholder = st.empty()
        if "log_placeholder" not in st.session_state:
            st.session_state["log_placeholder"] = log_placeholder
        else:
            log_placeholder = st.session_state["log_placeholder"]

        if log_placeholder is not None:
            log_placeholder.markdown("```\n[GUI] 等待启动...\n```")

        # ---- 状态与启动栏 ----
        bar_col1, bar_col2, bar_col3 = st.columns([2, 1, 2])
        with bar_col1:
            if st.button("启动研发", use_container_width=True):
                stop_router()
                start_router(log_placeholder)
                st.rerun()

        with bar_col2:
            current_state = read_status()
            state_emoji = {
                "idle": "🟢", "pending_classification": "🟡",
                "clarifying_requirements": "🟣", "pending_design_approval": "🔵",
            }
            emoji = state_emoji.get(current_state, "🟠")
            st.markdown(f"{emoji} **{current_state}**")

        with bar_col3:
            if st.button("停止调度中枢", use_container_width=True):
                stop_router()
                st.rerun()

        # ---- 需求输入区 ----
        st.subheader("需求输入")
        current_concept = ""
        if os.path.exists(CONCEPT_FILE):
            try:
                with open(CONCEPT_FILE, "r", encoding="utf-8") as f:
                    current_concept = f.read()
            except Exception:
                pass

        new_concept = st.text_area(
            "输入需求（修改后自动同步到 concept_brief.md）",
            value=current_concept,
            height=150,
            key="concept_input",
        )
        # 自动同步
        if new_concept.strip() != current_concept.strip():
            sync_concept_to_file(new_concept)
            st.caption("自动同步到 concept_brief.md")

    with col_right:
        st.header("下发文件目录")

        # ---- 加载 Meta 数据 ----
        meta = load_meta()
        sys_name = meta.get("system_name", "")
        tag = meta.get("primary_tag", "")
        ver = meta.get("version", "v1")
        if sys_name:
            st.caption(f"项目: **{tag}_{sys_name}_{ver}**")

        files = scan_workspace_files()
        if not files:
            st.info("暂无产出文件")
        else:
            # 按类型分组
            detail_files = [f for f in files if f.endswith((".md", ".mmd"))]
            data_files = [f for f in files if f.endswith(".json")]
            code_files = [f for f in files if f.endswith((".gd", ".py"))]
            other = [f for f in files if f not in detail_files + data_files + code_files]

            for group_name, group_files in [
                ("📄 文档", detail_files),
                ("📊 数据", data_files),
                ("💻 代码", code_files),
                ("📁 其他", other),
            ]:
                if group_files:
                    st.caption(group_name)
                    for f in group_files:
                        fp = os.path.join(WORKSPACE_DIR, f)
                        display_name = build_display_name(f, meta)
                        if st.button(display_name, key=f"ws_{f}", use_container_width=True):
                            open_file(fp)

# ================================================================
# 档案管理页面
# ================================================================

elif page == "档案管理":
    col_center, col_right = st.columns([6, 3])

    with col_center:
        st.header("知识库沉淀")

        doc_name = st.text_input("文档名字 / 提取锚点（文档必须在 .agent_workspace 文件夹内）", key="arch_doc")
        meta_comment = st.text_area("输入老板批注 (Meta-Comment)", key="arch_comment")

        btn_col1, btn_col2 = st.columns(2)
        list_type = None

        with btn_col1:
            if st.button("🔴 归入负向 (反面教训)", use_container_width=True):
                list_type = "black"
        with btn_col2:
            if st.button("🟢 归入正向 (优秀范式)", use_container_width=True):
                list_type = "red"

        if list_type and doc_name.strip():
            # 构建 archivist 参数
            arch_cmd = [
                sys.executable,
                os.path.join(ROOT_DIR, "Agents", "archivist_agent.py"),
                doc_name.strip(),
                "all",
                list_type,
                meta_comment.strip() or "（无评语）",
            ]
            with st.spinner(f"正在归档到{ '红榜' if list_type == 'red' else '黑榜' }..."):
                try:
                    result = subprocess.run(arch_cmd, capture_output=True, text=True, cwd=ROOT_DIR)
                    if result.returncode == 0:
                        st.toast(f"知识库沉淀成功！", icon="✅")
                    else:
                        st.error(f"归档失败: {result.stderr[-500:]}")
                except Exception as e:
                    st.error(f"执行异常: {e}")

    with col_right:
        st.header("知识库目录")

        # 优秀范式
        st.subheader("优秀范式")
        best_files = scan_knowledge(BEST_DIR)
        if best_files:
            for f in best_files:
                fp = os.path.join(BEST_DIR, f)
                if st.button(f" {f}", key=f"best_{f}", use_container_width=True):
                    open_file(fp)
        else:
            st.caption("（空）")

        st.divider()

        # 反面教训
        st.subheader("反面教训")
        anti_files = scan_knowledge(ANTI_DIR)
        if anti_files:
            for f in anti_files:
                fp = os.path.join(ANTI_DIR, f)
                if st.button(f" {f}", key=f"anti_{f}", use_container_width=True):
                    open_file(fp)
        else:
            st.caption("（空）")
