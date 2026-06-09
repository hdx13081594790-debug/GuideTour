from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# 全局配置中心。
#
# 数据流：
# .env / 环境变量 -> Settings(BaseSettings) -> get_settings()
# -> main.py、地图 Provider、Redis Store、DeepSeek Client 等模块读取配置。
#
# 所有需要随环境变化的值都应该放在这里，而不是写死在业务代码里。


class Settings(BaseSettings):
    # FastAPI 基础配置。
    app_name: str = "Summer Palace Guide"
    api_prefix: str = "/api/v1"

    # 数据层配置：默认 SQLite 方便本地演示，生产可替换 MySQL URL。
    database_url: str = Field("sqlite:///./summer_palace_guide.db", alias="DATABASE_URL")
    redis_url: str = Field("redis://localhost:6379/0", alias="REDIS_URL")

    # 地图配置：NavigationService 根据 map_provider 选择地图适配器。
    map_provider: str = Field("local", alias="MAP_PROVIDER")
    amap_key: str | None = Field(None, alias="AMAP_KEY")
    baidu_ak: str | None = Field(None, alias="BAIDU_AK")
    baidu_browser_ak: str | None = Field(None, alias="BAIDU_BROWSER_AK")
    route_fallback_local: bool = Field(True, alias="ROUTE_FALLBACK_LOCAL")

    # 大模型配置：GuideAgent 通过 DeepSeekAgentClient 使用这些值。
    deepseek_api_key: str | None = Field(None, alias="DEEPSEEK_API_KEY")
    deepseek_base_url: str = Field("https://api.deepseek.com", alias="DEEPSEEK_BASE_URL")
    deepseek_model: str = Field("deepseek-v4-flash", alias="DEEPSEEK_MODEL")
    jwt_secret: str = Field("dev-secret-change-me", alias="JWT_SECRET")
    auto_create_tables: bool = Field(True, alias="AUTO_CREATE_TABLES")

    model_config = SettingsConfigDict(env_file=".env", populate_by_name=True, extra="ignore")


@lru_cache
def get_settings() -> Settings:
    # 缓存 Settings，避免每次请求都重新解析 .env。
    # 如果测试里临时改环境变量，需要清理这个 cache 才能生效。
    return Settings()
