import os
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv('DB_URL')
if not DB_URL:
    raise ValueError('未配置DB_URL环境变量')

TORTOISE_ORM = {
    "connections": {
        "default": DB_URL
    },
    "apps": {
        "models": {
            "models": [
                    "aerich.models",
                    "app.db.resume_table",
                    "app.db.prompt_table", 
                    "app.db.candidate_table",
                    "app.db.skill_table"
                    ],
            "default_connection": "default",
        }
    },
}


# --- MinIO 配置 ---
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "127.0.0.1:9100")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET_NAME = "resumes"  # 你的桶名字
MINIO_SECURE = False  # 如果是 https 设为 True


# --- 大模型配置 (这里以 OpenAI 兼容接口为例，比如 DeepSeek 或 Moonshot) ---
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_BASE_URL = os.getenv("LLM_BASE_URL") # 示例地址
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME")
if not LLM_API_KEY:
    raise ValueError("未配置 LLM_API_KEY")
