"""
Archivist Agent (知识库档案管理员)
职责：从历史文档中提炼逻辑骨架 → 脱水去业务化 → 存入 Knowledge/ 优秀案例与错误案例。
用法：python Agents/archivist_agent.py <target_file> <anchor> <red|black> "<meta_comment>"
"""

import json
import os
import re
import sys
import time
import traceback

FILE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(FILE_DIR)
sys.path.insert(0, ROOT_DIR)
WORKSPACE_DIR = os.path.join(os.environ.get("AI_STUDIO_DATA_DIR", ROOT_DIR), ".agent_workspace")
META_FILE = os.path.join(WORKSPACE_DIR, "project_meta.json")

from Skills.llm_client import ask_llm

BEST_DIR  = os.path.join(os.environ.get("AI_STUDIO_DATA_DIR", ROOT_DIR), "Knowledge", "best_practices")
ANTI_DIR  = os.path.join(os.environ.get("AI_STUDIO_DATA_DIR", ROOT_DIR), "Knowledge", "anti_patterns")
PROMPT_FILE = os.path.join(FILE_DIR, "prompts", "archivist_prompt.md")

RED   = "\033[91m"
GRN   = "\033[92m"
YEL   = "\033[93m"
RESET = "\033[0m"


def loud_fail(msg: str):
    print(f"{RED}========== [Archivist] 致命错误 =========={RESET}")
    print(f"{RED}{msg}{RESET}")
    traceback.print_exc()
    print(f"{RED}=========================================={RESET}")
    sys.exit(1)


def extract_section(md_text: str, anchor: str) -> str:
    """
    从 MD 文本中精准截取指定标题的章节。
    支持多级标题匹配（# ~ ######）。
    """
    # 构造匹配各级标题的正则
    pattern = rf"^#{{1,6}}\s*{re.escape(anchor)}.*$"
    match = re.search(pattern, md_text, re.MULTILINE)
    if not match:
        return md_text  # 找不到则返回原文

    start = match.start()
    level = len(re.match(r"^#+", md_text[start:]).group())
    remaining = md_text[start + len(match.group()):]

    # 找下一个同级或更高级标题
    next_match = re.search(rf"^#{{{1,{level}}}}\s", remaining, re.MULTILINE)
    if next_match:
        end = start + len(match.group()) + next_match.start()
        return md_text[start:end].strip()
    else:
        return md_text[start:].strip()


def sanitize_filename(text: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', '_', text)[:40]


def main():
    # ========== 解析参数 ==========
    if len(sys.argv) < 4:
        print(f"{YEL}用法: python archivist_agent.py <target_file> <anchor|all> <red|black> [meta_comment]{RESET}")
        sys.exit(1)

    target_file = sys.argv[1]
    anchor = sys.argv[2]
    list_type = sys.argv[3].lower()
    meta_comment = sys.argv[4] if len(sys.argv) > 4 else "（无评语）"

    if list_type not in ("red", "black"):
        loud_fail(f"list_type 必须是 'red' 或 'black'，实际: {list_type}")

    # 支持相对路径（优先从 .agent_workspace 查找）
    if not os.path.isabs(target_file):
        target_file = os.path.join(WORKSPACE_DIR, target_file)
    if not os.path.exists(target_file):
        # 再从 ROOT_DIR 查找
        alt = os.path.join(ROOT_DIR, sys.argv[1])
        if os.path.exists(alt):
            target_file = alt
        else:
            loud_fail(f"目标文件不存在: {target_file} (也试过: {alt})")

    target_dir = BEST_DIR if list_type == "red" else ANTI_DIR
    os.makedirs(target_dir, exist_ok=True)

    # ========== 1. 读取目标文件 ==========
    with open(target_file, "r", encoding="utf-8") as f:
        full_text = f.read()

    # ========== 2. 精准截取 ==========
    if anchor != "all":
        extracted_text = extract_section(full_text, anchor)
        print(f"[Archivist] 锚点截取: [{anchor}] → {len(extracted_text)} 字符")
    else:
        extracted_text = full_text
        print(f"[Archivist] 全文模式: {len(extracted_text)} 字符")

    # ========== 3. 加载提示词 ==========
    if not os.path.exists(PROMPT_FILE):
        loud_fail(f"提示词文件不存在: {PROMPT_FILE}")
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        system_prompt = f.read().strip()

    user_prompt = (
        f"【归档评语】：{meta_comment}\n\n"
        f"【待提炼的文档片段】：\n\n{extracted_text}\n\n"
        f"请按优秀案例规范提取逻辑骨架。"
    )

    # ========== 4. 呼叫 LLM ==========
    print("[Archivist] 正在呼叫大模型进行脱水提纯...")
    try:
        result = ask_llm(system_prompt, user_prompt)
    except Exception:
        loud_fail("大模型调用失败")

    # ========== 5. 命名空间继承 + 自动落盘 ==========
    ts = str(int(time.time()))
    safe_anchor = sanitize_filename(anchor)
    label = "优秀案例" if list_type == "red" else "错误案例"

    # 读取 project_meta.json 获取系统命名空间
    ns_prefix = ""
    if os.path.exists(META_FILE):
        try:
            with open(META_FILE, "r", encoding="utf-8") as f:
                meta = json.load(f)
            tag = meta.get("primary_tag", "")
            name = meta.get("system_name", "")
            ver = meta.get("version", "v1")
            if name:
                parts = [p for p in [tag, name, ver] if p]
                ns_prefix = "_".join(parts) + "_"
        except Exception:
            pass

    filename = f"{ns_prefix}[{label}]_{safe_anchor}_{ts}.md"
    filepath = os.path.join(target_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        # 方案 2：错误案例由 Python 物理拼接原始文档，彻底杜绝大模型篡改
        if list_type == "black":
            appended_skeleton = (
                f"\n\n#### 🦴 【失败脱水骨架 (原样保留)】 [读取优先级：Low]\n"
                f"*(⚠️ 最高警告：以下为犯罪现场原貌，绝对不可作为正确格式参考！)*\n"
                f"```text\n{extracted_text.strip()}\n```\n"
            )
            final_content = result.strip() + appended_skeleton
        else:
            final_content = result.strip()
        f.write(final_content)

    print(f"{GRN}[Archivist] 记忆切片已归档: {filepath}{RESET}")
    print(f"[Archivist] 类别: {label} | 锚点: {anchor} | 大小: {len(result)} 字符")


if __name__ == "__main__":
    main()
