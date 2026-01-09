import json
from typing import Any, Dict
from app.prompts.resume_prompt_provider import ResumePromptProvider
from openai import AsyncOpenAI
from app.settings import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL_NAME
from app.utils.school_tier import infer_school_tier

client = AsyncOpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)


class LLMClient:
    @staticmethod
    def _extract_json(content: str) -> dict:
        """提取并解析 JSON"""
        if not content:
            raise ValueError("空响应")
        
        clean = content.replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(clean)
        except json.JSONDecodeError:
            start, end = clean.find("{"), clean.rfind("}")
            if start != -1 and end > start:
                return json.loads(clean[start:end + 1])
            raise

    @staticmethod
    async def _call_llm(messages: list[Dict[str, Any]]) -> str:
        """调用 LLM API"""
        response = await client.chat.completions.create(
            model=LLM_MODEL_NAME,
            messages=messages,
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        if not response.choices or not response.choices[0].message.content:
            raise ValueError("LLM 返回为空")
        
        return response.choices[0].message.content

    @staticmethod
    def _normalize_skills(skills: Any) -> list[str]:
        """标准化技能"""
        if isinstance(skills, str):
            normalized = skills.replace("，", ",").replace("、", ",").replace("；", ",").replace(";", ",").replace("\n", ",")
            return [s.strip() for s in normalized.split(",") if s.strip()]
        return [str(s).strip() for s in (skills or []) if str(s).strip()]

    @staticmethod
    def _normalize_data(data: dict) -> dict:
        """标准化数据"""
        data.setdefault("candidate_info", {})
        json_data = data.setdefault("json_data", {})
        edu = json_data.setdefault("education", {})

        # 毕业年份
        if year := edu.get("graduation_year"):
            digits = "".join(c for c in str(year) if c.isdigit())
            if len(digits) >= 4 and digits[:2] in ("19", "20"):
                edu["graduation_year"] = digits[:4]

        # 学校层次
        if not edu.get("schooltier"):
            edu["schooltier"] = infer_school_tier(edu.get("university"))

        # 技能列表
        json_data["skills"] = LLMClient._normalize_skills(json_data.get("skills"))

        return data

    @staticmethod
    async def parse_resume(resume_content: str, criteria_content: str) -> dict:
        """解析简历"""
        try:
            messages = ResumePromptProvider().build_messages(criteria_content, resume_content)
            content = await LLMClient._call_llm(messages)
            return LLMClient._normalize_data(LLMClient._extract_json(content))
        except Exception as e:
            return {"is_qualified": False, "error": str(e), "json_data": {}, "candidate_info": {}}