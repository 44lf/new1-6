from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    app_name: str = Field(
        "Resume Screening Service",
        validation_alias="APP_NAME",
    )

    database_url: str = Field(
        "sqlite://resumes.db",
        validation_alias="DATABASE_URL",
        description="Tortoise ORM connection string",
    )

    minio_endpoint: str = Field(
        "localhost:9000",
        validation_alias="MINIO_ENDPOINT",
    )
    minio_access_key: str = Field(
        "minioadmin",
        validation_alias="MINIO_ACCESS_KEY",
    )
    minio_secret_key: str = Field(
        "minioadmin",
        validation_alias="MINIO_SECRET_KEY",
    )
    minio_bucket: str = Field(
        "resumes",
        validation_alias="MINIO_BUCKET",
    )

    openai_api_key: str = Field(
        "changeme",
        validation_alias="OPENAI_API_KEY",
    )
    openai_base_url: str = Field(
        "",
        validation_alias="OPENAI_BASE_URL",
    )
    openai_model: str = Field(
        "gpt-4o-mini",
        validation_alias="OPENAI_MODEL",
    )

    default_prompt: str = Field(
        """请阅读简历，从中提取姓名、邮箱、电话、个人简介，
并判断候选人是否符合预选条件。
请以 JSON 返回：
{
  qualified: bool,
  name: str,
  email: str,
  phone: str,
  summary: str,
  notes: str
}
""",
        validation_alias="DEFAULT_PROMPT",
    )


settings = Settings()
