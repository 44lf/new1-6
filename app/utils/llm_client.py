import json
from typing import Any

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
    async def _call_llm(messages: list[dict], use_response_format: bool) -> str:
        params: dict[str, Any] = {
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
    async def parse_resume(resume_content: str, criteria_content: str) -> dict:
        """
        调用大模型解析简历
        """
        json_structure = {
            "is_qualified": "Boolean, true表示符合硬性要求",
            "candidate_info": {"name": "姓名", "phone": "电话", "email": "邮箱"},
            "json_data": {
                "education": {"university": "学校", "major": "专业", "graduation_year": "2024"},
                "education_history": [],
                "skills": ["技能1", "技能2"],
                "work_experience": [],
                "projects": [],
                "reason": "简短理由",
            },
        }

        system_instruction = (
            "你是一个专业的招聘助手。请根据筛选标准分析简历。\n"
            "【输出要求】\n"
            "1. 必须返回合法的 JSON 字符串。\n"
            "2. 不要包含 Markdown 标记（如 ```json），不要有任何解释文字。\n"
            "3. 缺失字段填 null。\n"
            f"{json.dumps(json_structure, ensure_ascii=False, indent=2)}"
        )

        user_message = (
            f"【岗位筛选标准】：\n{criteria_content}\n\n"
            f"------------------\n"
            f"【候选人简历内容】：\n{resume_content}"
        )

        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_message},
        ]

        content = ""
        try:
            # 优先使用 response_format；不支持则自动降级
            try:
                content = await LLMClient._call_llm(messages, use_response_format=True)
            except Exception as e:
                error_text = str(e)
                if "response_format" in error_text or "Unrecognized request argument" in error_text:
                    print("LLM 不支持 response_format，尝试降级调用")
                    content = await LLMClient._call_llm(messages, use_response_format=False)
                else:
                    raise

            parsed_data = LLMClient._extract_json(content)
            return LLMClient._normalize_data_no_regex(parsed_data)

        except json.JSONDecodeError:
            print(f"JSON解析失败，原始返回: {content}")
            return {
                "is_qualified": False,
                "candidate_info": {},
                "json_data": {"reason": "模型返回格式错误"},
            }
        except Exception as e:
            print(f"LLM 调用失败: {e}")
            return {
                "is_qualified": False,
                "error": str(e),
                "json_data": {},
                "candidate_info": {},
            }

    @staticmethod
    def _normalize_data_no_regex(data: dict) -> dict:
        """
        不使用正则清洗数据（并补齐结构，避免缺键导致“清洗了空气”）
        """
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
