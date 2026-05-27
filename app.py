"""
AI Studio OS - Web GUI (Streamlit)
像素级还原：直角边框、高对比度、硬朗极简。
HITL 审批通过 web_io 桥梁（.web_prompt.json / .web_response.json）的实现终端 ↔ Web 双向通信。
"""

import os, sys, json, time, subprocess, threading

if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
    except Exception: pass

import streamlit as st

# ---- 路径 ----
ROOT = os.path.dirname(os.path.abspath(__file__))
WS   = os.path.join(ROOT, ".agent_workspace")
KN   = os.path.join(ROOT, "Knowledge")
BEST = os.path.join(KN, "best_practices")
ANTI = os.path.join(KN, "anti_patterns")
CONCEPT_FILE  = os.path.join(WS, "concept_brief.md")
STATUS_FILE   = os.path.join(WS, "task_status.json")
PROMPT_FILE   = os.path.join(WS, ".web_prompt.json")
RESPONSE_FILE = os.path.join(WS, ".web_response.json")
LOG_FILE      = os.path.join(WS, ".web_log.jsonl")

# ---- 友好文件名映射 ----
LABEL_MAP = {
    "system_design_detail.md":     "系统详细案",
    "system_design_draft.md":      "主策宏观草案",
    "system_numerical_data.json":  "数值配置表",
    "system_numerical_docs.json":  "数值说明书",
    "system_schema.json":          "系统Schema",
    "system_flow.mmd":             "系统流程图",
    "tech_blueprint.md":           "程序开发蓝图",
    "task_plan.md":                "PM任务拆解",
    "task_status.json":            "任务状态",
    "concept_brief.md":            "概念简案",
    "audit_feedback.json":         "审查报告",
    "audit_trace_log.md":          "审查追踪",
    "ui_config.json":              "UI配置",
    "generated_skill.gd":          "生成代码",
    "project_meta.json":           "项目元数据",
    "review_board.md":             "验收表",
    "current_result.json":         "当前数据",
}
ICON = {".md":"M", ".mmd":"M", ".json":"{}", ".gd":"G", ".py":"P"}

# ---- 页面 ----
st.set_page_config(page_title="AI Studio OS", page_icon="🎮", layout="wide")

# ================================================================
# 硬核 CSS — 直角、高对比、冷峻
# ================================================================
st.markdown("""
<style>

* { border-radius:0 !important; box-shadow:none !important; font-family:"Microsoft YaHei","PingFang SC",sans-serif !important; }



/* 全局 */

body, .main, [data-testid="stAppViewContainer"], section[data-testid="stSidebar"] > div:first-child {

    background:#fff !important; color:#333 !important;

}



/* 侧边栏 — 深灰底白字, 220px */

[data-testid="stSidebar"] {

    background:#333 !important; min-width:220px !important; max-width:220px !important;

}

[data-testid="stSidebar"] * { color:#fff !important; }

[data-testid="stSidebar"] label[data-baseweb="radio"] div[role="radio"] {

    width:100% !important; padding:18px !important; font-size:18px !important;

    font-weight:bold !important; border:1px solid #555 !important;

    background:#444 !important; color:#ccc !important; margin-bottom:4px !important;

}

[data-testid="stSidebar"] label[data-baseweb="radio"] div[role="radio"][data-selected="true"] {

    background:#000 !important; color:#fff !important; border-color:#000 !important;

}



/* 按钮 */

div.stButton > button {

    font-weight:bold !important; font-size:16px !important; padding:10px 0 !important;

    width:100% !important; border:2px solid #333 !important;

}

div.stButton > button[kind="secondary"] {

    background:#ff3b30 !important; color:#fff !important; border-color:#cc0000 !important;

}



/* 日志 textarea */

div[data-testid="stTextArea"] textarea {

    font-family:"Consolas","Courier New",monospace !important; font-size:14px !important;

    line-height:1.5 !important; color:#333 !important; background:#fafafa !important;

    border:2px solid #555 !important;

}



/* chat_input 拉高到 4行 */

div[data-testid="stChatInput"] textarea { min-height:100px !important; line-height:1.5 !important; }

div[data-testid="stChatInput"] input { min-height:100px !important; line-height:1.5 !important; }



/* info box */

div[data-testid="stAlert"] { border-left:4px solid #000 !important; background:#f0f0f0 !important; }



/* 文件按钮 */

section[data-testid="stSidebar"] + div button[kind="secondary"] {

    background:#fff !important; color:#333 !important; border:none !important;

    text-align:left !important; font-size:13px !important; padding:8px 5px !important;

}

section[data-testid="stSidebar"] + div button[kind="secondary"]:hover { background:#eee !important; }



/* 标题 */

h3 { font-size:20px !important; font-weight:bold !important; border-bottom:1px solid #333 !important; padding-bottom:8px !important; margin-top:20px !important; }



/* ========================================================= */
/* 终极修复：height:100% 链式继承打通全屏 */
/* ========================================================= */
html, body, #root {
    height: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
}
.stApp {
    height: 100% !important;
}
[data-testid="stAppViewContainer"] {
    height: 100% !important;
    display: flex !important;
    flex-direction: column !important;
}
section.main, section[data-testid="stMain"] {
    min-height: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    flex-grow: 1 !important;
    overflow-y: auto !important;
}
.block-container {
    min-height: 100% !important;
    flex-grow: 1 !important;
    display: flex !important;
    flex-direction: column !important;
    padding-top: 2rem !important;
    padding-bottom: 2rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    max-width: 100% !important;
}

footer {
    display: none !important;
}

header[data-testid="stHeader"] { 
    display: none !important;
}

button { border-radius:0px !important; }

.stTextArea textarea { border-radius:0px !important; border:2px solid #555 !important; background-color:#fcfcfc !important; }

section[data-testid="stSidebar"] + div button[kind]:not([disabled]) { border:1px solid #ddd !important; background:#fff !important; color:#333 !important; text-align:left !important; padding-left:12px !important; }



/* 中栏 flex 布局：底部控制固定 */

.bottom-area { padding-top:10px !important; }

/* 控制栏垂直居中 */

/* ========================================================= */
/* 修复 2：撤销全局垂直居中，精准控制左右分栏与底部对齐 */
/* ========================================================= */
/* A. 将所有横向分栏恢复为【顶部对齐】，拯救右侧掉下来的文件列表 */
div[data-testid="stHorizontalBlock"] {
    align-items: flex-start !important; 
}

/* 强制列内部的元素绝对贴顶排布 */
div[data-testid="column"] > div[data-testid="stVerticalBlock"] {
    justify-content: flex-start !important;
}

/* B. 精准靶向治疗：仅让底部控制栏的那一行实现垂直居中 */
.bottom-area div[data-testid="stHorizontalBlock"] {
    align-items: center !important; 
}

/* 右栏文件按钮左对齐 */

[data-testid="stVerticalBlock"] button[kind] { text-align:left !important; padding-left:12px !important; }

/* 文件列表按钮左对齐 + 缩进 */

.st-emotion-cache button[kind="secondary"] { text-align:left !important; padding-left:12px !important; }

</style>
""", unsafe_allow_html=True)

# ================================================================
# 工具
# ================================================================

def read_state():
    try:
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("current_state", "idle")
    except: return "idle"

def sync_concept(text: str):
    try: os.makedirs(WS, exist_ok=True); open(CONCEPT_FILE, "w", encoding="utf-8").write(text.strip())
    except: pass

def open_local(fp):
    p = os.path.abspath(fp)
    if sys.platform == "win32": os.startfile(p)
    elif sys.platform == "darwin": subprocess.call(["open", p])
    else: subprocess.call(["xdg-open", p])

def is_running():
    p = st.session_state.get("router_proc")
    return p is not None and p.poll() is None

def get_prompt():
    if not os.path.exists(PROMPT_FILE): return None
    try:
        d = json.load(open(PROMPT_FILE, "r", encoding="utf-8"))
        return None if d.get("answered", False) else d
    except: return None

def submit_answer(ans: str):
    try: os.makedirs(WS, exist_ok=True); json.dump({"answer": ans, "ts": time.time()}, open(RESPONSE_FILE, "w", encoding="utf-8"))
    except: pass

def read_logs(n=80):
    if not is_running():
        return ["[System] 引擎未启动，点击 启动研发 开始"]
    if not os.path.exists(LOG_FILE): return ["[System] 等待引擎启动..."]
    try:
        raw = [l.strip() for l in open(LOG_FILE, "r", encoding="utf-8") if l.strip()]
        # 合并连续重复行
        merged = []
        for line in raw:
            if merged and line == merged[-1]:
                if merged[-1].endswith("×2"):
                    merged[-1] = merged[-1].replace("×2", "×3")
                elif "×" in merged[-1].rsplit("×", 1)[-1].strip().isdigit():
                    parts = merged[-1].rsplit("×", 1)
                    merged[-1] = f"{parts[0].strip()}×{int(parts[1])+1}"
                else:
                    merged[-1] = f"{line} ×2"
            else:
                merged.append(line)
        return merged[-n:] or ["[System] 等待引擎启动..."]
    except: return ["[System] 等待引擎启动..."]


def read_logs_str() -> str:
    return "\n".join(read_logs(200))

def scan_ws():
    """扫描产出文件：跳过框架文件 + 空占位 + 本轮启动前旧文件，按修改时间排序"""
    FRAMEWORK = {
        "blueprint.json", "active_schema.json", "current_result.json",
        "task_status.json", "review_board.md", "task_route.json",
        "boss_feedback.txt", "project_meta.json", "concept_brief.md",
    }
    if not os.path.exists(WS): return []
    since = st.session_state.get("engine_start_ts", 0)
    files = []
    for f in os.listdir(WS):
        fp = os.path.join(WS, f)
        if os.path.isfile(fp) and not f.startswith("."):
            if f in FRAMEWORK: continue
            mtime = os.path.getmtime(fp)
            if mtime < since: continue  # 本轮启动前的旧文件不显示
            if os.path.getsize(fp) > 10:
                files.append((f, mtime))
    files.sort(key=lambda x: x[1])
    return [f[0] for f in files]

def scan_kb(d):
    return sorted(os.listdir(d)) if os.path.exists(d) else []

def fmt_name(f):
    label = LABEL_MAP.get(f, f.rsplit(".", 1)[0])
    ext = "." + f.rsplit(".", 1)[-1] if "." in f else ""
    icon = ICON.get(ext, "-")
    return f"[{icon}] {label}"

# ---- Router 控制 ----

def start_engine():
    os.makedirs(WS, exist_ok=True)
    # 清除旧 web_io 通信残留 + 清空旧日志 + 清除概念缓存（确保 Router 冷启动触发）
    for f in [PROMPT_FILE, RESPONSE_FILE,
              os.path.join(WS, ".concept_brief_cache.txt")]:
        if os.path.exists(f):
            os.remove(f)
    open(LOG_FILE, "w", encoding="utf-8").close()
    try: open(LOG_FILE, "a", encoding="utf-8").write("[GUI] 引擎启动中...\n")
    except: pass
    st.session_state["engine_start_ts"] = time.time()
    st.session_state["display_state"] = "idle"  # 启动时重置状态显示
    env = os.environ.copy(); env["AI_STUDIO_WEB_MODE"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    p = subprocess.Popen(
        [sys.executable, "-u", os.path.join(ROOT, "main_router.py")],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        encoding="utf-8", errors="replace", cwd=ROOT, env=env,
    )
    st.session_state["router_proc"] = p
    def cap():
        try:
            for line in iter(p.stdout.readline, ""):
                if line and line.strip():
                    open(LOG_FILE, "a", encoding="utf-8").write(line.strip() + "\n")
        except: pass
    threading.Thread(target=cap, daemon=True).start()

def stop_engine():
    p = st.session_state.get("router_proc")
    if p and p.poll() is None:
        try: p.terminate(); p.wait(timeout=3)
        except:
            try: p.kill()
            except: pass

# ================================================================
# 侧边栏
# ================================================================

with st.sidebar:
    st.markdown("### 🎮 AI Studio OS")
    page = st.radio("导航", ["📝 写案子", "📚 记忆积累"], label_visibility="collapsed")

    st.divider()
    running = is_running()
    state = read_state()
    STATES = {"idle":"Idle","pending_classification":"分类中","clarifying_requirements":"追问中",
              "pending_design_approval":"草案审批","pending_plan_approval":"排期审批",
              "pending_system_design":"系统策划","pending_system_approval":"系统验收",
              "pending_schema_translate":"翻译中","pending_numerical":"数值推演",
              "pending_numerical_approval":"数值审批","pending_tech_design":"主程蓝图",
              "pending_tech_approval":"架构验收","completed":"完成"}
    label = STATES.get(state, state)
    st.caption(f"状态: {label}")

# ================================================================
# 写案子
# ================================================================

if page == "📝 写案子":
    L, C, R = st.columns([1.5, 6, 2.5])

    with C:
        # 标题
        st.markdown("### 显示终端反馈的那种log内容")

        # 日志（components.html 保留 script 标签，自动滚动）
        log_html = read_logs_str().replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
        st.components.v1.html(
            f"""
            <div id="logScroll" style="border:2px solid #555; background:#fafafa; padding:15px;
            font-family:Consolas,Courier New,monospace; font-size:14px; line-height:1.5;
            height:55vh; overflow-y:auto; color:#333;">{log_html}</div>
            <script>
            var el=document.getElementById('logScroll');
            if(el) el.scrollTop=el.scrollHeight;
            var observer=new MutationObserver(function(){{ el.scrollTop=el.scrollHeight; }});
            if(el) observer.observe(el,{{childList:true,subtree:true}});
            </script>
            """,
            height=390,
        )

        # 底部控制区
        st.markdown('<div class="bottom-area">', unsafe_allow_html=True)
        bc1, bc2, _ = st.columns([1, 1, 4])
        with bc1:
            if running:
                if st.button("⏹ 停止", key="stop", type="secondary", use_container_width=True):
                    stop_engine(); st.rerun()
            else:
                if st.button("启动研发", key="start", type="secondary", use_container_width=True):
                    start_engine(); st.rerun()
        with bc2:
            # 引擎未启动时使用上次存储的显示状态，启动后用实时状态
            if running:
                state_text = STATES.get(read_state(), "Unenable")
                st.session_state["display_state"] = state_text
            else:
                state_text = st.session_state.get("display_state", "Unenable")
            st.markdown(f"**{state_text}**")

        # ===== 单一输入框 (三态, chat_input Enter提交 + CSS拉高) =====
        prompt = get_prompt()
        actual_state = read_state()
        in_approval = any(kw in actual_state for kw in ["approval","clarify","system_design","plan","tech","numerical_appr"])

        if not running:
            cmd = st.chat_input("请输入指令 (Enter发送)")
            if cmd and cmd.strip():
                sync_concept(cmd.strip())
                start_engine()
                st.rerun()
        elif prompt and in_approval:
            st.info(f"🤖 **系统问询**\n\n{prompt.get('prompt','')}")
            reply = st.chat_input("请回复系统问询... (Enter发送)")
            if reply:
                submit_answer(reply); st.rerun()
        else:
            st.chat_input("AI 运行中...", disabled=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with R:
        st.markdown("### 下发文件")
        if running:
            files = scan_ws()
            if files:
                for f in files:
                    fp = os.path.join(WS, f)
                    if st.button(fmt_name(f), key=f"f_{f}", use_container_width=True):
                        open_local(fp)
            else:
                st.caption("（暂无文件）")
        else:
            st.caption("启动引擎后扫描...")

# ================================================================
# 记忆积累
# ================================================================

elif page == "📚 记忆积累":
    L, C, R = st.columns([1.5, 6, 2.5])

    with C:
        st.subheader("知识库沉淀")
        doc = st.text_input("文档名字 (在 .agent_workspace 内)", key="ad", placeholder="例: system_design_draft.md")
        com = st.text_area("老板批注", key="ac", placeholder="例: 本案状态机流转极其严谨")

        b1, b2 = st.columns(2)
        tp = None
        with b1:
            if st.button("🔴 归入黑榜", use_container_width=True): tp = "black"
        with b2:
            if st.button("🟢 归入红榜", use_container_width=True): tp = "red"

        if tp and doc.strip():
            cmd = [sys.executable, os.path.join(ROOT, "Agents", "archivist_agent.py"),
                   doc.strip(), "all", tp, com.strip() or "（无评语）"]
            with st.spinner("归档中..."):
                try:
                    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", cwd=ROOT)
                    if r.returncode == 0: st.success("归档成功！")
                    else: st.error(f"失败: {r.stderr[-300:]}")
                except Exception as e: st.error(f"异常: {e}")

    with R:
        st.subheader("🟢 红榜")
        for f in scan_kb(BEST):
            if st.button(f"📄 {f}", key=f"b_{f}", use_container_width=True): open_local(os.path.join(BEST, f))
        if not scan_kb(BEST): st.caption("（空）")
        st.divider()
        st.subheader("🔴 黑榜")
        for f in scan_kb(ANTI):
            if st.button(f"📄 {f}", key=f"a_{f}", use_container_width=True): open_local(os.path.join(ANTI, f))
        if not scan_kb(ANTI): st.caption("（空）")

# ---- 自刷新 ----
if is_running():
    time.sleep(2)
    st.rerun()
