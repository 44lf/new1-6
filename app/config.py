from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict

class Settings(BaseSettings):
    # v2 推荐：用 model_config 指定 .env
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # 你的 .env: APP_NAME（可选，没有就用默认）
    app_name: str = Field(default="Resume Screening Service", validation_alias="APP_NAME")

    # 你的 .env: DB_URL
    db_url: str = Field(
        default="sqlite:///./resumes.db",
        validation_alias="DB_URL",
        description="DB connection string, e.g. mysql://root:pwd@127.0.0.1:3306/db?charset=utf8mb4",
    )

    # 你的 .env: DB_GENERATE_SCHEMAS
    db_generate_schemas: bool = Field(default=False, validation_alias="DB_GENERATE_SCHEMAS")

    # 你的 .env: MINIO_*
    minio_endpoint: str = Field(default="127.0.0.1:9100", validation_alias="MINIO_ENDPOINT")
    minio_access_key: str = Field(default="minioadmin", validation_alias="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(default="minioadmin", validation_alias="MINIO_SECRET_KEY")
    minio_secure: bool = Field(default=False, validation_alias="MINIO_SECURE")

    # 你的 .env: 两个 bucket 分开
    minio_resume_bucket: str = Field(default="resumes", validation_alias="MINIO_RESUME_BUCKET")
    minio_image_bucket: str = Field(default="resume-images", validation_alias="MINIO_IMAGE_BUCKET")

    # 你的 .env: LLM_*
    llm_base_url: str = Field(default="https://api.deepseek.com", validation_alias="LLM_BASE_URL")
    llm_api_key: str = Field(default="", validation_alias="LLM_API_KEY")
    llm_model: str = Field(default="deepseek-chat", validation_alias="LLM_MODEL")


settings = Settings()
