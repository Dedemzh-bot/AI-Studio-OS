"""
UI Agent (UX/UI 全栈设计师)
职责：读取已通过安检的技能数值数据，输出纯平面的 UI 视觉与 UX 布局配置。
严格剥离引擎动效（粒子、震动、缓动曲线等），只负责平面设计层。
输出：ui_config.json
"""

import json
import os
import re
import sys
import traceback

# ---- 强制绝对路径：基于本文件位置推算项目根目录 ----
FILE_DIR = os.path.dirname(os.path.abspath(__file__))       # Agents/
ROOT_DIR = os.path.dirname(FILE_DIR)                         # 项目根目录
sys.path.insert(0, ROOT_DIR)

from Skills.llm_client import ask_llm
from Skills.rag_loader import load_knowledge_with_context

# ---- 所有读写目标均拼装为绝对路径 ----
WORKSPACE_DIR = os.path.join(os.environ.get("AI_STUDIO_DATA_DIR", ROOT_DIR), ".agent_workspace")
RESULT_FILE   = os.path.join(WORKSPACE_DIR, "current_result.json")
OUTPUT_FILE   = os.path.join(WORKSPACE_DIR, "ui_config.json")
STATUS_FILE   = os.path.join(WORKSPACE_DIR, "task_status.json")

RED   = "\033[91m"
RESET = "\033[0m"


def loud_fail(msg: str):
    """大声打印红色错误 + 完整 Traceback，然后 sys.exit(1) 通知 Router"""
    print(f"{RED}========== [UI Agent] 致命错误 =========={RESET}")
    print(f"{RED}{msg}{RESET}")
    traceback.print_exc()
    print(f"{RED}=========================================={RESET}")
    sys.exit(1)


def main():
    # ========== 1. 读取已通过安检的技能底层数值数据 ==========
    try:
        if not os.path.exists(RESULT_FILE):
            loud_fail(f"底层数据文件不存在: {RESULT_FILE}")

        with open(RESULT_FILE, "r", encoding="utf-8") as f:
            pristine_data = json.load(f)

        print(f"[UI Agent] 已读取底层数据")
        print(f"[UI Agent] 文件路径: {RESULT_FILE}")
        print(f"[UI Agent] 来源 Agent: {pristine_data.get('source_agent', 'unknown')}")
        print(f"[UI Agent] 任务 ID: {pristine_data.get('task_id', 'unknown')}")

    except json.JSONDecodeError:
        loud_fail(f"底层数据 JSON 解析失败: {RESULT_FILE}")
    except Exception:
        loud_fail(f"读取底层数据失败: {RESULT_FILE}")

    payload = pristine_data.get("payload")
    if payload is None:
        loud_fail("底层数据中缺少 payload 字段，无法设计 UI 表现")

    payload_json_str = json.dumps(payload, ensure_ascii=False, indent=2)

    # ========== 2. 构建 UX/UI 全栈设计师人设提示词 ==========
    system_prompt = """你是一位资深的游戏 UX/UI 全栈设计师。你需要读取底层技能数据，为其输出一套纯平面的 UI 视觉和 UX 布局配置文件。

绝对禁止包含任何屏幕震动、粒子特效、缓动曲线等引擎内动效（Motion）设定。你只负责平面设计层，引擎动效由动效师在另一条管线单独处理。

必须输出纯粹的 JSON，包含以下四大结构：

1. "ux_layout" — UX 布局信息：
   - component_type: 组件类型（如 "skill_card"）
   - hierarchy: 数组，描述从上到下的排版层级（如 ["icon", "title", "tags", "description"]）

2. "ui_tokens" — UI 视觉令牌：
   - theme_color: 契合技能属性的 Hex 颜色代码（如 "#FF4444" 火、 "#4488FF" 冰、 "#44FF44" 毒、 "#FFDD44" 电）
   - bg_material: 背景材质风格（如 "solid"、"glassmorphism"、"gradient_radial"、"dark_metallic"）
   - typography_style: 字体排印风格描述（如 "bold_title_large, body_regular, number_monospace"）

3. "assets_and_content" — 资源与文案：
   - icon_prompt: 精准的 AI 绘画提示词（英文），用于生成技能图标，格式为 "game icon, skill, ..."
   - rich_text_desc: 含 <color=Hex>数值</color> 标签的富文本技能描述，将底层数值嵌入其中

4. "screen_position" — 屏幕锚定位置：
   - anchor: 组件相对于父级面板的锚点位置。请根据技能用途智能推断：
     * 主动技能卡片 (skill_card) → "center" 或 "bottom_center"
     * 被动 Buff 图标 → "top_left" 或 "top_right"
     * 警告弹窗或大招提示 → "center" 或 "center_top"
     * 可使用以下值之一: center, top_left, top_center, top_right, center_left, center_right, bottom_left, bottom_center, bottom_right
   - offset_x: 相对于锚点的 X 轴偏移量（整数，像素单位），正值向右
   - offset_y: 相对于锚点的 Y 轴偏移量（整数，像素单位），正值向下

最高指令：
1. 禁止废话，禁止解释，禁止问候语
2. 只输出合法的纯 JSON，不要加 Markdown 标记
3. 颜色选择必须符合技能属性直觉
4. 图标提示词必须是英文，风格统一"""

    user_prompt = f"""以下是一个游戏技能的底层数值数据（JSON 格式）：

```json
{payload_json_str}
```

请根据以上数据，输出一套完整的纯平面 UI/UX 配置文件（包含 ux_layout、ui_tokens、assets_and_content、screen_position 四大结构）。直接输出 JSON。"""

    # ========== 3. 注入 RAG 知识上下文 ==========
    rag_context = load_knowledge_with_context(ROOT_DIR, task_domain="界面UI")
    if rag_context:
        user_prompt += f"\n\n{rag_context}"
        print(f"[UI Agent] 已注入 RAG 上下文 ({len(rag_context)} 字符)")
    else:
        print("[UI Agent] RAG 知识库为空（无匹配领域的案例）")

    # ========== 4. 调用大模型 ==========
    print("[UI Agent] 正在呼叫大模型设计前端表现配置...")
    try:
        llm_response = ask_llm(system_prompt, user_prompt)
    except Exception:
        loud_fail("大模型调用失败（网络超时 / API Key 无效 / 服务不可用）")

    # 不管返回什么，先强制打印原始返回值
    print("=" * 60)
    print("【大模型原始返回】:")
    print(llm_response)
    print("=" * 60)
    print(f"[UI Agent] 大模型返回完成 ({len(llm_response)} 字符)")

    # ========== 4. 正则精准提取 JSON ==========
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", llm_response, re.DOTALL)

    if json_match:
        clean_json_str = json_match.group(1).strip()
        print(f"[UI Agent] 正则成功提取 JSON ({len(clean_json_str)} 字符)")
    else:
        clean_json_str = llm_response.strip()
        print("[UI Agent] 未找到代码块标记，使用原始返回值")

    # 验证 JSON 合法性
    try:
        ui_data = json.loads(clean_json_str)
    except json.JSONDecodeError:
        loud_fail(f"大模型返回的不是合法 JSON！完整原始返回:\n{llm_response}")

    # ========== 5. 保存 UI 表现配置文件 ==========
    try:
        os.makedirs(WORKSPACE_DIR, exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(ui_data, f, ensure_ascii=False, indent=2)
        print(f"[UI Agent] UI 表现配置已保存至: {OUTPUT_FILE}")

        # 逐字段打印验证（三大结构）
        print("[UI Agent] --- ux_layout ---")
        layout = ui_data.get("ux_layout", {})
        print(f"[UI Agent]   component_type: {layout.get('component_type', '(缺失)')}")
        print(f"[UI Agent]   hierarchy: {layout.get('hierarchy', '(缺失)')}")

        print("[UI Agent] --- ui_tokens ---")
        tokens = ui_data.get("ui_tokens", {})
        for tk in ["theme_color", "bg_material", "typography_style"]:
            val = tokens.get(tk, "(缺失)")
            print(f"[UI Agent]   {tk}: {val}")

        print("[UI Agent] --- assets_and_content ---")
        assets = ui_data.get("assets_and_content", {})
        for ak in ["icon_prompt", "rich_text_desc"]:
            val = assets.get(ak, "(缺失)")
            if isinstance(val, str) and len(val) > 80:
                val = val[:80] + "..."
            print(f"[UI Agent]   {ak}: {val}")

        print("[UI Agent] --- screen_position ---")
        pos = ui_data.get("screen_position", {})
        for pk in ["anchor", "offset_x", "offset_y"]:
            print(f"[UI Agent]   {pk}: {pos.get(pk, '(缺失)')}")

    except Exception:
        loud_fail(f"写入 UI 配置文件失败: {OUTPUT_FILE}")

    # ========== 6. 推动流水线 ==========
    try:
        if not os.path.exists(STATUS_FILE):
            loud_fail(f"任务状态文件不存在: {STATUS_FILE}")

        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            status_data = json.load(f)

        current_state = status_data.get("current_state", "")
        status_data["current_state"] = "ui_done"

        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(status_data, f, ensure_ascii=False, indent=2)

        print(f"[UI Agent] 任务状态已更新: {current_state} -> ui_done")
        print("[UI Agent] UI 表现设计工作完成。")

    except Exception:
        loud_fail(f"更新任务状态失败: {STATUS_FILE}")


if __name__ == "__main__":
    main()
