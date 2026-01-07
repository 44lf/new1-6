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
    async def parse_resume(resume_content: str, prompt_content: str) -> dict:
        """
        调用大模型解析简历
        :param resume_content: 简历的纯文本内容
        :param prompt_content: 提示词（Prompt）
        :return: 解析后的字典 (Dict)
        """
        
        # 组装系统级 Prompt，强制要求 JSON
        system_instruction = (
            "你是一个专业的简历解析助手。\n"
            "请严格按照用户的要求提取信息。\n"
            "【重要】你必须只返回纯粹的 JSON 字符串，不要包含 ```json ... ``` 标记，也不要包含其他废话。"
        )

        # 组装用户消息
        user_message = (
            f"提示词要求：\n{prompt_content}\n\n"
            f"简历内容：\n{resume_content}"
        )

        try:
            response = await client.chat.completions.create(
                model=LLM_MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.1, # 低温度保证输出稳定
                response_format={"type": "json_object"} # 如果模型支持 JSON Mode 最好开启
            )
            
            content = response.choices[0].message.content
            
            # 尝试解析 JSON
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # 容错：如果模型还是返回了 ```json 包裹，尝试清洗
                clean_content = content.replace("```json", "").replace("```", "").strip()
                return json.loads(clean_content)
                
        except Exception as e:
            print(f"LLM 调用失败: {e}")
            # 返回一个空的结构防止程序崩溃
            return {
                "is_qualified": False, 
                "error": str(e),
                "json_data": {},
                "candidate_info": {}
            }