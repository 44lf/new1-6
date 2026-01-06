from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    app_name: str = Field("Resume Screening Service", env="APP_NAME")
    database_url: str = Field(
        "sqlite:///./resumes.db",
        env="DATABASE_URL",
        description="SQLAlchemy connection string",
    )
    minio_endpoint: str = Field("localhost:9000", env="MINIO_ENDPOINT")
    minio_access_key: str = Field("minioadmin", env="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field("minioadmin", env="MINIO_SECRET_KEY")
    minio_bucket: str = Field("resumes", env="MINIO_BUCKET")
    deepseek_api_url: str = Field(
        "https://api.deepseek.com/v1/analyze", env="DEEPSEEK_API_URL"
    )
    deepseek_api_key: str = Field("changeme", env="DEEPSEEK_API_KEY")

    class Config:
        env_file = ".env"


settings = Settings()
