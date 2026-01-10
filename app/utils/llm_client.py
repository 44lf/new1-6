# app/utils/llm_client.py - 修复异常处理
import json
from openai import AsyncOpenAI
from app.settings import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL_NAME
from app.utils.helpers import normalize_skills, extract_year
from app.enums.education import infer_school_tier, normalize_school_tier


client = AsyncOpenAI(
    api_key=LLM_API_KEY,
    base_url=LLM_BASE_URL
)


class LLMClient:

    @staticmethod
    def _build_system_prompt() -> str:
        return """你是一个专业的招聘助手，负责解析简历并输出结构化结果。

【输出要求】
1. 只返回 JSON 对象，不要任何 Markdown 标记或解释文字
2. 缺失字段填 null，列表字段缺失返回空数组 []
3. 不要编造简历中不存在的信息

【JSON 结构】
{
  "is_qualified": true,
  "name": "张三",
  "phone": "13800138000",
  "email": "zhangsan@example.com",
  "university": "清华大学",
  "degree": "本科",
  "major": "计算机科学与技术",
  "graduation_year": "2024",
  "skills": ["python", "java", "mysql"],
  "work_experience": ["工作经历1", "工作经历2"],
  "projects": ["项目1", "项目2"],
  "score": 85,
  "reason": "符合要求的简短理由"
}

【特别注意】
- skills 必须是字符串数组，每个元素是单一技能，全部小写
- 不要包含"精通"、"熟悉"等描述词
- graduation_year 只填4位数字年份"""

    @staticmethod
    def _build_user_prompt(criteria: str, resume_text: str) -> str:
        return f"""【岗位筛选标准】
{criteria}

-------------------

【候选人简历内容】
{resume_text}"""

    @staticmethod
    async def _call_api(system_prompt: str, user_prompt: str) -> str:
        response = await client.chat.completions.create(
            model=LLM_MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )

        if not response.choices or not response.choices[0].message.content:
            raise ValueError("LLM 返回内容为空")

        return response.choices[0].message.content

    @staticmethod
    def _parse_json(content: str) -> dict:
        clean = content.replace("```json", "").replace("```", "").strip()

        try:
            return json.loads(clean)
        except json.JSONDecodeError:
            start = clean.find("{")
            end = clean.rfind("}")
            if start != -1 and end > start:
                return json.loads(clean[start:end + 1])
            raise ValueError("无法解析 LLM 返回的 JSON")

    @staticmethod
    def _normalize_result(data: dict) -> dict:
        """【修复 Bug 5】标准化 LLM 返回的结果"""
        # 1. 技能标准化
        if "skills" in data:
            data["skills"] = normalize_skills(data["skills"])

        # 2. 毕业年份提取
        if "graduation_year" in data:
            data["graduation_year"] = extract_year(data["graduation_year"])

        # 3. 学校层次推断（确保一定有值）
        tier = normalize_school_tier(data.get("schooltier"))
        if not tier or tier.value == "null":
            tier = infer_school_tier(data.get("university"))

        # 【修复】如果还是 None，设置为 "null" 字符串而不是 None
        # 这样可以在数据库中明确表示"未知"
        if tier:
            data["schooltier"] = tier.value
        else:
            data["schooltier"] = "null"

        # 4. 确保必需字段存在
        data.setdefault("is_qualified", False)
        data.setdefault("score", 0)

        return data

    @staticmethod
    async def parse_resume(resume_text: str, criteria: str) -> dict:
        """
        【修复 Bug 5】解析简历 - 改进异常处理
        """
        try:
            system_prompt = LLMClient._build_system_prompt()
            user_prompt = LLMClient._build_user_prompt(criteria, resume_text)
            content = await LLMClient._call_api(system_prompt, user_prompt)
            data = LLMClient._parse_json(content)
            data = LLMClient._normalize_result(data)
            return data

        except Exception as e:
            # 【修复】出错时也要确保 schooltier 有默认值
            print(f"LLM 解析失败: {e}")
            return {
                "is_qualified": False,
                "name": None,
                "phone": None,
                "email": None,
                "university": None,
                "schooltier": "null",  # 明确设置为 "null" 而不是 None
                "degree": None,
                "major": None,
                "graduation_year": None,
                "skills": [],
                "work_experience": [],
                "projects": [],
                "score": 0,
                "reason": f"解析失败: {str(e)}"
            }