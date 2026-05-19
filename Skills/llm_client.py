"""
LLM Client (大模型底层通道)
职责：整个 AI Studio OS 中所有 Agent 调用大模型思考的唯一入口。
基于 openai 库 + python-dotenv，支持 DeepSeek 等兼容 API。
"""

import os
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

# ---- 加载 .env ----
# 从项目根目录加载环境变量
_env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=_env_path)

LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")

if not LLM_API_KEY:
    raise RuntimeError(
        f"未找到 LLM_API_KEY，请检查 {_env_path} 文件是否配置正确"
    )

# ---- 初始化 Client ----
_client = OpenAI(
    api_key=LLM_API_KEY,
    base_url=LLM_BASE_URL,
)

# ---- 配置 ----
DEFAULT_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")
DEFAULT_TEMPERATURE = 0.3
DEFAULT_MAX_TOKENS = 8192
MAX_RETRIES = 3
RETRY_DELAY = 2  # 重试等待秒数（指数递增）


def ask_llm(
    system_prompt: str,
    user_prompt: str,
    *,
    model: str = DEFAULT_MODEL,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> str:
    """
    所有 Agent 调用大模型的唯一底层通道。

    参数:
        system_prompt: 系统角色提示词（设定人设与铁律）
        user_prompt:   用户级提示词（具体任务内容）
        model:         模型名（默认 deepseek-chat）
        temperature:   生成温度（默认 0.3，保证输出稳定性）
        max_tokens:    最大输出 token 数

    返回:
        LLM 响应的文本内容（已去除首尾空白）

    异常:
        连续重试 MAX_RETRIES 次后仍失败则抛出 RuntimeError
    """
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = _client.chat.completions.create(
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            content = response.choices[0].message.content or ""
            return content.strip()

        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES:
                wait = RETRY_DELAY * attempt
                print(
                    f"[LLM Client] 第 {attempt} 次调用失败: {e}，"
                    f"{wait} 秒后重试 (共 {MAX_RETRIES} 次)..."
                )
                time.sleep(wait)
            else:
                print(f"[LLM Client] 已重试 {MAX_RETRIES} 次，全部失败。")

    # 所有重试耗尽
    raise RuntimeError(
        f"LLM 调用失败，已重试 {MAX_RETRIES} 次。"
        f"最后错误: {last_error}"
    )
