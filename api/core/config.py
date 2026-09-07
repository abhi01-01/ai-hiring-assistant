from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "AI Hiring Assistant API"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    MOCK_CANDIDATE_PHONE: str | None = None

    DATABASE_URL: str
    DB_POOL_SIZE: int = Field(default=10, ge=1, le=50)
    DB_MAX_OVERFLOW: int = Field(default=20, ge=0, le=100)
    DB_POOL_TIMEOUT: int = Field(default=30, ge=1, le=120)
    DB_AUTO_CREATE: bool = False
    DB_AUTO_MIGRATE: bool = False

    CORS_ORIGINS: str = "http://localhost:3000"
    PUBLIC_BASE_URL: str = "http://localhost:8000"

    HUNAR_API_KEY: str = ""
    DEFAULT_AGENT_ID: str = ""

    HUNAR_HTTP_TIMEOUT: float = Field(
        default=30.0,
        gt=0,
        le=120,
    )

    HUNAR_WEBHOOK_URL: str = ""
    HUNAR_WEBHOOK_SECRET: str = ""

    CANDIDATE_SEARCH_PROVIDER: str = ""
    APOLLO_API_KEY: str = ""
    APOLLO_BASE_URL: str = "https://api.apollo.io/api/v1"
    APOLLO_PER_PAGE: int = Field(default=10, ge=1, le=100)
    APOLLO_ENRICH_RESULTS: bool = True
    APOLLO_HTTP_TIMEOUT: float = Field(default=20.0, gt=0, le=120)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.CORS_ORIGINS.split(",") if item.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
