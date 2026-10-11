from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "Qingwen"
    DEBUG: bool = True
    ENV: str = "dev"

    CORS_ORIGINS: list[str] = ["*"]

    # LLM
    DEEPSEEK_API_KEY: str = ""
    DASHSCOPE_API_KEY: str = ""
    DEFAULT_LLM: str = "deepseek"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://qingwen:qingwen_dev_pwd@localhost:5432/qingwen"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7


settings = Settings()