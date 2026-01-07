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
        :param resume_content: 简历的纯文本内容
        :param criteria_content: 数据库里的岗位筛选标准 (仅包含要求，不含格式指令)
        :return: 解析后的字典 (Dict)
        """

        # === 1. 定义强制的输出结构 (Hardcoded Schema) ===
        # 这里定义了后端 Service 层所需的完整字段结构
        json_structure = {
            "is_qualified": "Boolean, true表示符合硬性要求，false表示不符合",
            "candidate_info": {
                "name": "候选人真实姓名",
                "phone": "电话号码",
                "email": "邮箱地址"
            },
            "json_data": {
                "education": {
                    "university": "最高学历毕业院校",
                    "major": "专业名称",
                    "graduation_year": "毕业年份 (例如 2024)"
                },
                #历史学历
                "education_history": [
                    {
                        "university": "学校名称",
                        "major": "专业",
                        "degree": "学历 (本科/硕士/博士)",
                        "start": "开始年份",
                        "end": "结束年份"
                    }
                ],
                "skills": ["技能1", "技能2", "技能3"],
                "work_experience": [
                    {
                        "company": "公司名称",
                        "role": "职位",
                        "start": "开始时间",
                        "end": "结束时间",
                        "description": "简要工作描述"
                    }
                ],
                "projects": [
                    {
                        "name": "项目名称",
                        "description": "项目描述"
                    }
                ],
                "reason": "判断合格或不合格的简短理由 (20字以内)"
            }
        }

        # === 2. 组装 System Prompt ===
        system_instruction = (
            "你是一个专业的招聘与简历解析助手。\n"
            "你的任务是根据用户提供的【筛选标准】分析【简历内容】。\n"
            "------------------\n"
            "【输出格式严格要求】\n"
            "1. 你必须，且只能返回一段合法的 JSON 字符串。\n"
            "2. 不要使用 markdown 标记（如 ```json），不要包含任何解释性文字。\n"
            "3. 必须严格遵守以下 JSON 结构，如果简历中缺少某些字段，请填 null 或 空字符串：\n"
            f"{json.dumps(json_structure, ensure_ascii=False, indent=2)}"
        )

        # === 3. 组装 User Message ===
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
                temperature=0.1, # 低温度保证格式稳定
                response_format={"type": "json_object"} # 强制 JSON 模式
            )

            content = response.choices[0].message.content

            # 清洗与解析
            try:
                # 再次防止模型有时候还会加 markdown
                clean_content = content.replace("```json", "").replace("```", "").strip()
                return json.loads(clean_content)
            except json.JSONDecodeError:
                print(f"JSON解析失败，原始返回: {content}")
                return {
                    "is_qualified": False,
                    "candidate_info": {},
                    "json_data": {"reason": "模型返回格式错误"}
                }

        except Exception as e:
            print(f"LLM 调用失败: {e}")
            return {
                "is_qualified": False,
                "error": str(e),
                "json_data": {},
                "candidate_info": {}
            }