from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Summer Palace Guide"
    api_prefix: str = "/api/v1"
    database_url: str = Field("sqlite:///./summer_palace_guide.db", alias="DATABASE_URL")
    redis_url: str = Field("redis://localhost:6379/0", alias="REDIS_URL")
    map_provider: str = Field("local", alias="MAP_PROVIDER")
    amap_key: str | None = Field(None, alias="AMAP_KEY")
    baidu_ak: str | None = Field(None, alias="BAIDU_AK")
    baidu_browser_ak: str | None = Field(None, alias="BAIDU_BROWSER_AK")
    route_fallback_local: bool = Field(True, alias="ROUTE_FALLBACK_LOCAL")
    jwt_secret: str = Field("dev-secret-change-me", alias="JWT_SECRET")
    auto_create_tables: bool = Field(True, alias="AUTO_CREATE_TABLES")

    model_config = SettingsConfigDict(env_file=".env", populate_by_name=True, extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
