import json
from typing import Any, Dict

from openai import AsyncOpenAI

from app.config import settings


class LLMService:
    def __init__(self) -> None:
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key, base_url=settings.openai_base_url or None
        )

    async def analyze_resume(self, resume_text: str, prompt: str) -> Dict[str, Any]:
        system_prompt = (
            "你是一个专业的人才筛选助手。请根据用户提供的提示词和简历原文，返回 JSON 对象，"
            "必须只包含字段：qualified (bool), name (string), email (string), phone (string), "
            "summary (string), notes (string), avatar (base64 PNG string，可为空)。"
        )
        message = f"{prompt}\n\n=== 简历全文 ===\n{resume_text}\n\n请严格按指定字段返回 JSON。"

        response = await self.client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content or "{}"
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {}
