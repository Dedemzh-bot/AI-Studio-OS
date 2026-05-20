"""
System Planner (系统架构师 / 设计草案)
职责：读取概念简案 + 全局记忆 → 输出人类可读的 system_design_draft.md
绝不输出 JSON Schema，只负责可讨论的 MD 草案。
"""

import json
import os
import sys
import traceback

FILE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(FILE_DIR)
sys.path.insert(0, ROOT_DIR)

from Skills.llm_client import ask_llm

WORKSPACE_DIR  = os.path.join(ROOT_DIR, ".agent_workspace")
CONCEPT_FILE   = os.path.join(WORKSPACE_DIR, "concept_brief.md")
CODEX_FILE     = os.path.join(WORKSPACE_DIR, "project_codex.md")
REGISTRY_FILE  = os.path.join(WORKSPACE_DIR, "global_asset_registry.json")
DRAFT_OUTPUT   = os.path.join(WORKSPACE_DIR, "system_design_draft.md")
FEEDBACK_FILE  = os.path.join(WORKSPACE_DIR, "boss_feedback.txt")
STATUS_FILE    = os.path.join(WORKSPACE_DIR, "task_status.json")

RED   = "\033[91m"
GRN   = "\033[92m"
RESET = "\033[0m"


def loud_fail(msg: str):
    print(f"{RED}========== [System Planner] 致命错误 =========={RESET}")
    print(f"{RED}{msg}{RESET}")
    traceback.print_exc()
    print(f"{RED}=============================================={RESET}")
    sys.exit(1)


def main():
    # ========== 1. 读取概念简案 ==========
    try:
        if not os.path.exists(CONCEPT_FILE):
            loud_fail(f"概念简案文件不存在: {CONCEPT_FILE}")
        with open(CONCEPT_FILE, "r", encoding="utf-8") as f:
            concept_text = f.read().strip()
        if not concept_text:
            loud_fail("概念简案内容为空")
        print(f"[System Planner] 已读取概念简案 ({len(concept_text)} 字符)")
    except Exception:
        loud_fail(f"读取概念简案失败: {CONCEPT_FILE}")

    # ========== 1.5. 加载全局记忆 ==========
    codex_text = ""
    if os.path.exists(CODEX_FILE):
        try:
            with open(CODEX_FILE, "r", encoding="utf-8") as f:
                codex_text = f.read().strip()
            if codex_text:
                print(f"[System Planner] 已加载项目记忆 Codex ({len(codex_text)} 字符)")
        except Exception:
            pass

    registry_text = ""
    if os.path.exists(REGISTRY_FILE):
        try:
            with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
                registry_text = f.read()
            if len(registry_text) > 100:
                registry_text = registry_text[:5000]
                print(f"[System Planner] 已加载全局资产字典 (截取 {len(registry_text)} 字符)")
        except Exception:
            pass

    # ========== 1.6. 读取老板反馈（如果有） ==========
    feedback_text = ""
    if os.path.exists(FEEDBACK_FILE):
        try:
            with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
                feedback_text = f.read().strip()
            if feedback_text:
                print(f"[System Planner] 已读取老板修改意见 ({len(feedback_text)} 字符)")
        except Exception:
            pass

    # ========== 2. 构建提示词（仅输出 MD 草案） ==========
    system_prompt = """你是一位顶级游戏系统功能负责人，承接主策划宏观草案，负责铺陈极其详细的玩法规则。

你的唯一任务：将主策划草案中的大框架，铺设成带有清晰条件分支、判定规则、玩家操作流程的 Markdown 详细设计文档。

输出格式：纯 Markdown 文档。必须包含以下章节：

## 1. 系统概述
- 系统名称、定位、核心玩法闭环简述

## 2. 详细玩法规则
- 每个子玩法的触发条件、判定逻辑、成功/失败条件、分数计算规则
- 如果有小游戏，必须描述具体的操作步骤和判定机制

## 3. 模块划分与条件分支
- 每个核心模块的名称、职责、与其他模块的关系
- 明确写出每个模块内部的条件分支（如：if 公会等级 >= 3 → 解锁深水区）

## 4. 数值成长维度
- 列出所有需要数值策划填表的成长维度，标明是连续成长（随等级递增）还是离散解锁（特定等级触发）
- 包含各维度的取值范围建议

## 5. 核心字段说明
- 每个模块的关键字段名称、类型、含义、示例值

## 6. 系统流程
- 用文字描述完整的用户操作流程和系统状态流转

最高指令：
1. 仅输出 Markdown 文档，绝对不要输出 JSON、Mermaid 或任何代码块
2. 所有字段名建议使用英文 snake_case
3. 参考全局记忆中已有的系统，确保新设计能与旧系统联动
4. 禁止设计任何运行时状态字段（如 current_exp、timestamp 等）
5. 【严禁越权】禁止在文档结尾生成任何"下游任务拆解（WBS）"、"PM 派单指令"或"后续执行建议"。你只负责把玩法规则讲透，不负责替老板分派工作。"""

    user_prompt = f"以下是老板的系统玩法需求：\n\n---\n{concept_text}\n---\n\n请输出一份完整的系统设计草案（Markdown 格式）。"

    if feedback_text:
        user_prompt = (
            f"【老板修改意见】：{feedback_text}\n\n"
            "请根据以上意见重新修改设计草案。\n\n"
            f"{user_prompt}"
        )

    if codex_text:
        user_prompt = (
            "【全局项目记忆】：\n"
            f"{codex_text}\n\n"
            "---\n\n"
            f"{user_prompt}"
        )

    if registry_text:
        user_prompt += f"\n\n【已有资产登记表】：\n```json\n{registry_text}\n```"

    # ========== 3. 调用大模型 ==========
    print("[System Planner] 正在呼叫大模型生成系统设计草案...")
    try:
        llm_response = ask_llm(system_prompt, user_prompt)
    except Exception:
        loud_fail("大模型调用失败")

    print("=" * 60)
    print("【大模型原始返回】:")
    print(llm_response[:500])
    if len(llm_response) > 500:
        print(f"... (共 {len(llm_response)} 字符)")
    print("=" * 60)

    if not llm_response.strip():
        loud_fail("大模型返回了空内容")

    # ========== 4. 保存 MD 草案 ==========
    try:
        os.makedirs(WORKSPACE_DIR, exist_ok=True)
        with open(DRAFT_OUTPUT, "w", encoding="utf-8") as f:
            f.write(llm_response.strip())
        print(f"{GRN}[System Planner] 设计草案已保存: {DRAFT_OUTPUT} ({len(llm_response)} 字符){RESET}")
    except Exception:
        loud_fail(f"写入草案失败: {DRAFT_OUTPUT}")

    # ========== 5. 推动流水线 ==========
    try:
        if not os.path.exists(STATUS_FILE):
            loud_fail(f"任务状态文件不存在: {STATUS_FILE}")
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            status_data = json.load(f)
        current_state = status_data.get("current_state", "")
        status_data["current_state"] = "pending_system_approval"
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(status_data, f, ensure_ascii=False, indent=2)
        print(f"[System Planner] 任务状态: {current_state} -> pending_system_approval")
        print("[System Planner] 详细设计草案已完成，等待老板系统验收。")
    except Exception:
        loud_fail(f"更新状态失败: {STATUS_FILE}")


if __name__ == "__main__":
    main()
