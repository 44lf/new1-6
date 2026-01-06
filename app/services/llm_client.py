import httpx

from app.config import settings


class LLMService:
    async def analyze_resume(self, resume_text: str, prompt: str) -> dict:
        """
        Send resume text to the configured DeepSeek endpoint and return structured data.
        The expected response schema:
        {
            "qualified": bool,
            "name": str,
            "email": str,
            "phone": str,
            "summary": str,
            "notes": str,
            "avatar": "base64 encoded image or url"
        }
        """
        headers = {"Authorization": f"Bearer {settings.deepseek_api_key}"}
        payload = {"prompt": prompt, "resume": resume_text}

        async with httpx.AsyncClient() as client:
            response = await client.post(settings.deepseek_api_url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
