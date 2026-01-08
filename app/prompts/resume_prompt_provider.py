# app/prompts/resume_prompt_provider.py
import json
from typing import Any, Dict, List

class ResumePromptProvider:
    @staticmethod
    def json_structure() -> Dict[str, Any]:
        return {
            "is_qualified": "Boolean, true表示符合硬性要求",
            "candidate_info": {"name": "姓名", "phone": "电话", "email": "邮箱"},
            "json_data": {
                "education": {
                    "university": "学校",
                    "schooltier": "学校层次",
                    "degree": "学历",
                    "major": "专业",
                    "graduation_year": "2024",
                },
                "education_history": [],
                "skills": ["技能1", "技能2"],
                "work_experience": [],
                "projects": [],
                "reason": "简短理由",
            },
        }

    @staticmethod
    def system_instruction(json_structure: Dict[str, Any]) -> str:
        return (
            "你是一个专业的招聘助手，负责根据筛选标准解析简历并输出结构化结果。\n"
            "【输出要求】\n"
            "1. 必须返回合法的 JSON 字符串（根对象必须是 JSON object）。\n"
            "2. 不要包含 Markdown 标记（如 ```json），不要输出任何解释文字。\n"
            "3. 除 schooltier 外，其他缺失字段一律填 null；列表字段缺失则返回空数组 []。\n"
            "4. 不要编造简历中不存在的信息。\n"
            "\n"
            "【schooltier 判定（非常重要）】\n"
            "A. 仅依据“最终学历对应的毕业院校”判断：最高学历为本科→看本科院校；硕士/博士→看硕/博院校。\n"
            "B. schooltier 只能取以下之一：\"985/211\"、\"双一流\"、\"普通本科\"、\"专科\"、null。\n"
            "C. 若无法从简历文本中明确判断院校层次，必须输出 null（不允许猜测）。\n"
            "\n"
            "【输出 JSON 结构】\n"
            f"{json.dumps(json_structure, ensure_ascii=False, indent=2)}"
        )

    @staticmethod
    def user_message(criteria_content: str, resume_content: str) -> str:
        return (
            f"【岗位筛选标准】：\n{criteria_content}\n\n"
            f"------------------\n"
            f"【候选人简历内容】：\n{resume_content}"
        )

    @classmethod
    def build_messages(cls, criteria_content: str, resume_content: str) -> List[dict]:
        schema = cls.json_structure()
        return [
            {"role": "system", "content": cls.system_instruction(schema)},
            {"role": "user", "content": cls.user_message(criteria_content, resume_content)},
        ]
