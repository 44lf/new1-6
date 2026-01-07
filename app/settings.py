import os

DB_URL='mysql://root:123456@127.0.0.1:3306/project1?charset=utf8mb4'

TORTOISE_ORM = {
    "connections": {
        # 这里直接引用上面的变量
        "default": DB_URL
    },
    "apps": {
        "models": {
            # 告诉它去哪里找你写的 class Resume...
            # 如果你的 models.py 和 settings.py 在同一级目录，这就写 ["models"]
            "models": [
                    "app.db.resume_table",
                    "app.db.prompt_table", 
                    "app.db.candidate_table"
                    ],
            "default_connection": "default",
        }
    },
}


# --- MinIO 配置 ---
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "127.0.0.1:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET_NAME = "resumes"  # 你的桶名字
MINIO_SECURE = False  # 如果是 https 设为 True



# --- 大模型配置 (这里以 OpenAI 兼容接口为例，比如 DeepSeek 或 Moonshot) ---
LLM_API_KEY = os.getenv("LLM_API_KEY", "sk-effdfa994395427e8999e6f3c561c2e3")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1") # 示例地址
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "deepseek-chat")