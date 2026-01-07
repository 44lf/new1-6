import json
from openai import AsyncOpenAI # type: ignore
from app.settings import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL_NAME

# 初始化异步客户端
client = AsyncOpenAI(
    api_key=LLM_API_KEY,
    base_url=LLM_BASE_URL
)

class LLMClient:
    @staticmethod
    async def parse_resume(resume_content: str, criteria_content: str) -> dict:
        """
        调用大模型解析简历
        """
        # === 1. 定义输出结构 (Schema) ===
        json_structure = {
            "is_qualified": "Boolean, true表示符合硬性要求",
            "candidate_info": {
                "name": "姓名",
                "phone": "电话",
                "email": "邮箱"
            },
            "json_data": {
                "education": {
                    "university": "学校",
                    "major": "专业",
                    "graduation_year": "2024"
                },
                "education_history": [],
                "skills": ["技能1", "技能2"],
                "work_experience": [],
                "projects": [],
                "reason": "简短理由"
            }
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

        try:
            response = await client.chat.completions.create(
                model=LLM_MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content

            # 1. 提取 JSON (纯字符串操作)
            parsed_data = LLMClient._extract_json_no_regex(content)

            if not parsed_data:
                # 如果失败，构造一个带有错误信息的返回
                return {
                    "is_qualified": False,
                    "error": f"无法解析JSON，原始内容: {content[:100]}...", # 只截取前100字避免日志太长
                    "candidate_info": {},
                    "json_data": {}
                }

            # 2. 数据清洗 (纯字符串操作)
            final_data = LLMClient._normalize_data_no_regex(parsed_data)
            return final_data

        except Exception as e:
            print(f"LLM 调用失败: {e}")
            return {
                "is_qualified": False,
                "error": str(e),
                "json_data": {},
                "candidate_info": {}
            }

    @staticmethod
    def _extract_json_no_regex(text: str) -> dict:
        """
        不使用正则提取 JSON：
        利用 find('{') 找开头，rfind('}') 找结尾，然后截取中间部分。
        """
        if not text:
            return None

        # 1. 去除首尾空白
        text = text.strip()

        # 2. 寻找最外层的花括号
        start_index = text.find('{')
        end_index = text.rfind('}')

        if start_index != -1 and end_index != -1 and end_index > start_index:
            # 截取可能是 JSON 的部分
            possible_json = text[start_index : end_index + 1]
            try:
                return json.loads(possible_json)
            except json.JSONDecodeError:
                pass

        # 3. 最后的尝试：也许整个字符串就是 JSON (比如纯数字或列表，虽不符合Schema但防个万一)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _normalize_data_no_regex(data: dict) -> dict:
        """
        不使用正则清洗数据
        """
        json_data = data.get("json_data", {})

        # --- 清洗毕业年份 ---
        # 目标：从 "2024年6月" 或 "2024" 中提取出 2024
        edu = json_data.get("education", {})
        if edu and "graduation_year" in edu:
            raw_val = str(edu["graduation_year"])
            # 提取字符串里的所有数字
            digits = "".join([c for c in raw_val if c.isdigit()])

            # 简单逻辑：如果提取出的数字像年份（4位，19xx或20xx），就采用
            if len(digits) >= 4:
                year_candidate = digits[:4] # 取前4位
                if year_candidate.startswith("19") or year_candidate.startswith("20"):
                    edu["graduation_year"] = year_candidate

        # --- 清洗技能列表 ---
        # 目标：把 "Python, Java, C++" (字符串) 变成 ["Python", "Java", "C++"] (列表)
        skills = json_data.get("skills")
        if isinstance(skills, str):
            # 1. 统一分隔符：把中文逗号、顿号、换行符都替换成英文逗号
            normalized_str = (skills.replace('，', ',')
                                    .replace('、', ',')
                                    .replace('；', ',')
                                    .replace(';', ',')
                                    .replace('\n', ','))

            # 2. 拆分并去空
            json_data["skills"] = [s.strip() for s in normalized_str.split(',') if s.strip()]

        elif not isinstance(skills, list):
            # 如果既不是字符串也不是列表（比如是 None），给个空列表
            json_data["skills"] = []

        return data