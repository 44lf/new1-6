from pydantic import BaseSettings, Field, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = Field("Resume Screening Service", env="APP_NAME")
    database_url: str = Field(
        "sqlite://resumes.db",
        env="DATABASE_URL",
        description="Tortoise ORM connection string",
    )
    minio_endpoint: str = Field("localhost:9000", env="MINIO_ENDPOINT")
    minio_access_key: str = Field("minioadmin", env="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field("minioadmin", env="MINIO_SECRET_KEY")
    minio_bucket: str = Field("resumes", env="MINIO_BUCKET")
    openai_api_key: str = Field("changeme", env="OPENAI_API_KEY")
    openai_base_url: str = Field("", env="OPENAI_BASE_URL")
    openai_model: str = Field("gpt-4o-mini", env="OPENAI_MODEL")
    default_prompt: str = Field(
        "请阅读简历，从中提取姓名、邮箱、电话、个人简介，并判断候选人是否符合预选条件。"
        "请以JSON返回：{qualified: bool, name: str, email: str, phone: str, summary: str, notes: str, avatar: base64_png_string}",
        env="DEFAULT_PROMPT",
    )

settings = Settings()
