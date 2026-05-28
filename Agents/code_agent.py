"""
Code Agent (程序执行)
职责：读取已通过 Guard 强校验的无暇数据，机械翻译为 Godot GDScript 代码。
不进行创意设计，只做纯翻译。无权修改设计意图。
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

# ---- 所有读写目标均拼装为绝对路径 ----
WORKSPACE_DIR = os.path.join(os.environ.get("AI_STUDIO_DATA_DIR", ROOT_DIR), ".agent_workspace")
RESULT_FILE   = os.path.join(WORKSPACE_DIR, "current_result.json")
OUTPUT_FILE   = os.path.join(WORKSPACE_DIR, "generated_skill.gd")
STATUS_FILE   = os.path.join(WORKSPACE_DIR, "task_status.json")

RED   = "\033[91m"
RESET = "\033[0m"


def loud_fail(msg: str):
    """大声打印红色错误 + 完整 Traceback，然后 sys.exit(1) 通知 Router"""
    print(f"{RED}========== [Code Agent] 致命错误 =========={RESET}")
    print(f"{RED}{msg}{RESET}")
    traceback.print_exc()
    print(f"{RED}==========================================={RESET}")
    sys.exit(1)


def main():
    # ========== 1. 读取已通过 Guard 强校验的无暇数据 ==========
    try:
        if not os.path.exists(RESULT_FILE):
            loud_fail(f"无暇数据文件不存在: {RESULT_FILE}")

        with open(RESULT_FILE, "r", encoding="utf-8") as f:
            pristine_data = json.load(f)

        print(f"[Code Agent] 已读取无暇数据")
        print(f"[Code Agent] 文件路径: {RESULT_FILE}")
        print(f"[Code Agent] 来源 Agent: {pristine_data.get('source_agent', 'unknown')}")
        print(f"[Code Agent] 任务 ID: {pristine_data.get('task_id', 'unknown')}")

    except json.JSONDecodeError:
        loud_fail(f"无暇数据 JSON 解析失败（理论上不应该发生，Guard 已校验过）: {RESULT_FILE}")
    except Exception:
        loud_fail(f"读取无暇数据失败: {RESULT_FILE}")

    # 提取 payload（实际的设计数据）
    payload = pristine_data.get("payload")
    if payload is None:
        loud_fail("无暇数据中缺少 payload 字段，无法翻译")

    # 转为格式化 JSON 字符串供大模型阅读
    payload_json_str = json.dumps(payload, ensure_ascii=False, indent=2)

    # ========== 2. 构建程序员人设提示词 ==========
    system_prompt = """你是一个资深的游戏客户端引擎开发工程师，Godot 4 的 GDScript 专家。

最高指令：
1. 禁止废话，禁止解释，禁止问候语
2. 只允许输出带有 ```gdscript 和 ``` 包裹的纯代码块
3. 代码必须是完整可运行的 Godot 4 GDScript 类（extends Node 或其他基类）
4. 严格遵循输入 JSON 中的设计规格，不擅自添加未定义的行为
5. 变量命名清晰，代码结构简洁，符合 GDScript 官方风格指南
6. 机械翻译，不要发挥创意"""

    user_prompt = f"""以下是一份已经过严格校验的游戏设计数据（JSON 格式）：

```json
{payload_json_str}
```

请将以上设计数据翻译为一个 Godot 4 GDScript 技能脚本类。
输出格式必须是：
```gdscript
你的纯代码
```

禁止输出任何其他内容。"""

    # ========== 3. 调用大模型 ==========
    print("[Code Agent] 正在呼叫大模型翻译代码...")
    try:
        llm_response = ask_llm(system_prompt, user_prompt)
    except Exception:
        loud_fail("大模型调用失败（网络超时 / API Key 无效 / 服务不可用）")

    # 不管返回什么，先强制打印原始返回值
    print("=" * 60)
    print("【大模型原始返回】:")
    print(llm_response)
    print("=" * 60)
    print(f"[Code Agent] 大模型返回完成 ({len(llm_response)} 字符)")

    # ========== 4. 正则精准提取代码块 ==========
    # 匹配 ```gdscript ... ``` 或 ``` ... ``` 代码块
    code_match = re.search(r"```(?:gdscript|GDScript)?\s*([\s\S]*?)\s*```", llm_response, re.DOTALL)

    if code_match:
        clean_code = code_match.group(1).strip()
        print(f"[Code Agent] 正则成功提取代码块 ({len(clean_code)} 字符)")
    else:
        # 如果大模型没加代码块标记，尝试把整段当代码用
        print("[Code Agent] 警告：未找到 ```gdscript ``` 代码块，使用原始返回值作为代码")
        clean_code = llm_response.strip()

    if not clean_code:
        loud_fail("提取到的代码内容为空！")

    # ========== 5. 保存生成的代码文件 ==========
    try:
        os.makedirs(WORKSPACE_DIR, exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(clean_code)
        print(f"[Code Agent] 代码已保存至: {OUTPUT_FILE}")
        print(f"[Code Agent] 代码长度: {len(clean_code)} 字符 / {len(clean_code.splitlines())} 行")

    except Exception:
        loud_fail(f"写入代码文件失败: {OUTPUT_FILE}")

    # ========== 6. 推动流水线 → completed ==========
    try:
        if not os.path.exists(STATUS_FILE):
            loud_fail(f"任务状态文件不存在: {STATUS_FILE}")

        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            status_data = json.load(f)

        current_state = status_data.get("current_state", "")
        status_data["current_state"] = "completed"

        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(status_data, f, ensure_ascii=False, indent=2)

        print(f"[Code Agent] 任务状态已更新: {current_state} -> completed")
        print("[Code Agent] 代码翻译工作完成，流水线终点。")

    except Exception:
        loud_fail(f"更新任务状态失败: {STATUS_FILE}")


if __name__ == "__main__":
    main()
