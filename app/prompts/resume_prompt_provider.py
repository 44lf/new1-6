# app/prompts/resume_prompt_provider.py
import json
from typing import Any, Dict, List
from .base import BasePromptProvider  # 导入刚才定义的基类

class ResumePromptProvider(BasePromptProvider):
    def get_json_structure(self) -> Dict[str, Any]:
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
                "skills": ["技能名1", "技能名2"],
                "work_experience": [],
                "projects": [],
                "reason": "简短理由",
            },
        }

    def _system_instruction(self) -> str:
        # 这是一个内部辅助方法
        schema = self.get_json_structure()
        return (
            "你是一个专业的招聘助手，负责根据筛选标准解析简历并输出结构化结果。\n"
            "【输出要求】\n"
            "1. 必须返回合法的 JSON 字符串（根对象必须是 JSON object）。\n"
            "2. 不要包含 Markdown 标记（如 ```json），不要输出任何解释文字。\n"
            "3. 除 schooltier 外，其他缺失字段一律填 null；列表字段缺失则返回空数组 []。\n"
            "4. 不要编造简历中不存在的信息。\n"
            "\n"
            "【schooltier 判定（非常重要）】\n"
            "1. 仅依据“最终学历对应的毕业院校”判断：最高学历为本科→看本科院校；硕士/博士→看硕/博院校。\n"
            "2. schooltier 只能取以下之一：\"985/211\"、\"双一流\"、\"普通本科\"、\"专科\"、null。\n"
            "3. 请根据提取到的毕业院校名称，利用你的通用知识判断该校是否属于“985/211”或“双一流”。若确实无法判定，才输出 null。\n"
            "\n"
             "【skliis 判定（非常重要）】\n"
            "1. skills 必须是字符串数组 string[]，只允许输出“技能标签”，不允许输出句子或描述、简历不存在的信息。\n"
            '2. 每个技能标签只包含“名词/术语/产品名/工具名/框架名/语言名”，禁止包含：掌握/精通/熟悉/了解/能够/应用/使用/经验/能力/理论/核心组件/数据治理/维度建模/等/等方面/相关 等描述性词语。\n'
            "3. 禁止包含连接词或结构：与/及/和/以及/、/（用于拼接多个技能）。一个元素只能表达一个技能。\n"
            '示例：["sql","hadoop","etl","linux","shell","airflow","spark","flink","tableau","数据仓库","维度建模"]\n'
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