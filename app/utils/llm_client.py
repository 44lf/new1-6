import json
from typing import Any, Dict,List
from app.prompts.base import BasePromptProvider
from openai import AsyncOpenAI  # type: ignore
from app.settings import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL_NAME


# 初始化异步客户端
client = AsyncOpenAI(
    api_key=LLM_API_KEY,
    base_url=LLM_BASE_URL,
)


class LLMClient:
    @staticmethod
    def _extract_json(content: str) -> dict:
        """
        兼容：
        - 纯 JSON
        - ```json ... ``` 包裹
        - JSON 前后夹杂少量文本（截取最外层 {}）
        """
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
        prompt_provider: BasePromptProvider  # <--- 核心改动：依赖注入
    ) -> dict:
        """
        现在这个方法不知道具体的 Prompt 是怎么构建的，它只负责调用 provider.build_messages
        """
        # 使用注入进来的 provider 生成消息
        messages = prompt_provider.build_messages(criteria_content, resume_content)

        content = ""
        try:
            # ... 下面的调用逻辑保持不变 ...
            try:
                content = await LLMClient._call_llm(messages, use_response_format=True)
            except Exception as e:
                # ... 错误处理逻辑保持不变 ...
                pass # (此处省略具体代码以节省篇幅)

            parsed_data = LLMClient._extract_json(content)
            return LLMClient._normalize_data_no_regex(parsed_data)

        except Exception as e:
            # ... 异常处理保持不变 ...
            return {"is_qualified": False, "error": str(e), "json_data": {}, "candidate_info": {}}

    @staticmethod
    def _normalize_data_no_regex(data: dict) -> dict:

        data.setdefault("candidate_info", {})
        json_data = data.setdefault("json_data", {})

        # --- 清洗毕业年份 ---
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

        # --- 清洗技能列表 ---
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
