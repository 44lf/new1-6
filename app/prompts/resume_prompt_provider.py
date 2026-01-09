# app/prompts/resume_prompt_provider.py
import json
from typing import Any, Dict, List

class ResumePromptProvider:
    def get_json_structure(self) -> Dict[str, Any]:
        #返回一个字典，将llm输出结构返回
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
                    "education_history":"过往教育经历"
                },
                "skills": ["技能名1", "技能名2"],
                "work_experience": ["工作经历1","工作经历2"],
                "projects": ["项目1","项目2"],
                "reason": "简短理由",
                "score":"岗位匹配分数"
            },
        }

    def _system_instruction(self) -> str:
        #内部辅助方法，不对外暴露，提高可读性、复用性
        schema = self.get_json_structure()
        #返回一个字符串，将llm规则为字符串返回，json.dumps会将字典转成json的字符串
        return (
            "你是一个专业的招聘助手，负责根据筛选标准解析简历并输出结构化结果。\n"
            "【输出要求】\n"
            "1. 只返回 JSON object，不要 Markdown 或解释文字。\n"
            "2. 除 schooltier 外，缺失字段填 null；列表字段缺失返回空数组 []。\n"
            "3. 不要编造简历中不存在的信息。\n"
            "\n"
            "【schooltier 规则】\n"
            "1. 仅依据最终学历对应的毕业院校判断。\n"
            "2. 只允许输出：\"985/211\"、\"双一流\"、\"普通本科\"、\"专科\"、null。\n"
            "\n"
            "【skills 规则】\n"
            "1. skills 必须是 string[]，每个元素是单一技能标签。\n"
            "2. 禁止包含描述性词语或连接词（如 精通/熟悉/与/及/和/以及/、）。\n"
            '示例：["sql","hadoop","etl","linux","airflow","spark"]\n'
            "\n"
            "【score 规则】\n"
            "1. score 必须是 0-100 的整数。\n"
            "\n"
            "【工作/项目经历】\n"
            "1. work_experience、projects 必须是 string[]。\n"
            "\n"
            "【输出 JSON 结构】\n"
            f"{json.dumps(schema, ensure_ascii=False, indent=2)}"
        )

    def _user_message(self, criteria_content: str, resume_content: str) -> str:
        return (
            f"【岗位筛选标准】：\n{criteria_content}\n\n"
            f"------------------\n"
            f"【候选人简历内容】：\n{resume_content}"
        )

    def build_messages(self, criteria_content: str, resume_content: str) -> List[dict]:
        # 实现接口方法
        return [
            {"role": "system", "content": self._system_instruction()},
            {"role": "user", "content": self._user_message(criteria_content, resume_content)},
        ]
