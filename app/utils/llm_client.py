import json
from typing import Any, Dict, List
from app.prompts.resume_prompt_provider import ResumePromptProvider
from openai import AsyncOpenAI  # type: ignore
from app.settings import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL_NAME
from app.utils.school_tier import infer_school_tier


# 初始化异步客户端
client = AsyncOpenAI(
    api_key=LLM_API_KEY,
    base_url=LLM_BASE_URL,
)


class LLMClient:
    @staticmethod
    def build_resume_messages(criteria_content: str, resume_content: str) -> list[Dict[str, Any]]:
        return ResumePromptProvider().build_messages(criteria_content, resume_content)

    @staticmethod
    def _extract_json(content: str) -> dict:

        if not content:
            raise ValueError("空响应内容，无法解析 JSON")

        clean_content = content.replace("```json", "").replace("```", "").strip()

        # 1) 直接解析
        try:
            obj = json.loads(clean_content)
            if isinstance(obj, dict):
                return obj
            raise json.JSONDecodeError("JSON is not an object", clean_content, 0)
        except json.JSONDecodeError:
            pass

        # 2) 截取最外层 {}
        start = clean_content.find("{")
        end = clean_content.rfind("}")
        if start == -1 or end == -1 or start >= end:
            raise json.JSONDecodeError("No JSON object found", clean_content, 0)

        obj = json.loads(clean_content[start : end + 1])
        if not isinstance(obj, dict):
            raise json.JSONDecodeError("JSON is not an object", clean_content, 0)
        return obj

    @staticmethod
    async def _call_llm(messages: list[Dict[str, Any]], use_response_format: bool) -> str:
        params: Dict[str, Any] = {
            "model": LLM_MODEL_NAME,
            "messages": messages,
            "temperature": 0.1,
        }

        if use_response_format:
            params["response_format"] = {"type": "json_object"}

        response = await client.chat.completions.create(**params)
        if not response.choices:
            raise ValueError("LLM 未返回可用的候选结果")

        content = response.choices[0].message.content
        if content is None:
            raise ValueError("LLM 返回内容为空")
        return content

    @staticmethod
    async def parse_resume(
        resume_content: str,
        criteria_content: str,
    ) -> dict:

        messages = LLMClient.build_resume_messages(criteria_content, resume_content)

        content = ""
        try:
            try:
                content = await LLMClient._call_llm(messages, use_response_format=True)
            except Exception as e:
                pass

            parsed_data = LLMClient._extract_json(content)
            return LLMClient._normalize_data_no_regex(parsed_data)

        except Exception as e:

            return {"is_qualified": False, "error": str(e), "json_data": {}, "candidate_info": {}}

    @staticmethod
    def _normalize_data_no_regex(data: dict) -> dict:

        data.setdefault("candidate_info", {})
        json_data = data.setdefault("json_data", {})

        # 清洗毕业年份
        edu = json_data.get("education")
        if not isinstance(edu, dict):
            edu = {}
            json_data["education"] = edu

        if "graduation_year" in edu and edu["graduation_year"] is not None:
            raw_val = str(edu["graduation_year"])
            digits = "".join([c for c in raw_val if c.isdigit()])
            if len(digits) >= 4:
                year_candidate = digits[:4]
                if year_candidate.startswith("19") or year_candidate.startswith("20"):
                    edu["graduation_year"] = year_candidate

        # 补全学校层次
        if edu.get("schooltier") is None:
            edu["schooltier"] = infer_school_tier(edu.get("university"))

        # 清洗技能列表
        skills = json_data.get("skills")
        if isinstance(skills, str):
            normalized_str = (
                skills.replace("，", ",")
                .replace("、", ",")
                .replace("；", ",")
                .replace(";", ",")
                .replace("\n", ",")
            )
            json_data["skills"] = [s.strip() for s in normalized_str.split(",") if s.strip()]
        elif isinstance(skills, list):
            json_data["skills"] = [str(s).strip() for s in skills if str(s).strip()]
        else:
            json_data["skills"] = []

        return data
