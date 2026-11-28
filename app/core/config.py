"""使用 Pydantic Settings 统一加载和校验应用配置。"""

from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field, PostgresDsn, SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class _BaseSettings(BaseSettings):
    """环境变量优先于项目根目录的 .env 文件，字段名不区分大小写。"""

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class AppSettings(_BaseSettings):
    """应用名称、调试模式和监听地址配置。"""

    app_name: str = Field(default="agent-service", alias="APP_NAME")
    app_debug: bool = Field(default=False, alias="APP_DEBUG")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8001, ge=1, le=65535, alias="APP_PORT")

class DatabaseSettings(_BaseSettings):
    """数据库相关设置"""

    host: str = Field(alias="DB_HOST", default="localhost")
    port: int = Field(alias="DB_PORT", default=5432)
    name: str = Field(alias="DB_NAME", default="insurance")
    user: str = Field(alias="DB_USER", default="insurance")
    password: str = Field(alias="DB_PASSWORD", default="insurance123")
    echo: bool = Field(alias="DB_ECHO", default=False)
    pool_size: int = Field(alias="DB_POOL_SIZE", default=5)
    max_overflow: int = Field(alias="DB_MAX_OVERFLOW", default=10)
    pool_timeout: int = Field(alias="DB_POOL_TIMEOUT", default=30)
    pool_recycle: int = Field(alias="DB_POOL_RECYCLE", default=1800)

    def build_url(self, scheme: str) -> str:
        return PostgresDsn.build(
            scheme=scheme,
            host=self.host,
            port=self.port,
            username=self.user,
            password=self.password,
            path=self.name,
        ).encoded_string()

    @computed_field
    @property
    def url(self) -> str:
        return self.build_url("postgresql+asyncpg")

    @computed_field
    @property
    def checkpoint_url(self) -> str:
        return self.build_url("postgresql")

class LLMSettings(_BaseSettings):
    """大语言模型及 API 密钥配置。"""

    deepseek_api_key: SecretStr
    chat_model: str = "deepseek-v4-flash"


class LoggingSettings(_BaseSettings):
    """日志输出配置。"""

    logging_level: str = "INFO"


@lru_cache(maxsize=1)
def get_app_settings() -> AppSettings:
    """获取缓存的应用配置。"""
    return AppSettings()


@lru_cache(maxsize=1)
def get_database_settings() -> DatabaseSettings:
    """获取缓存的数据库配置。"""
    return DatabaseSettings()


@lru_cache(maxsize=1)
def get_llm_settings() -> LLMSettings:
    """获取缓存的大语言模型配置。"""
    return LLMSettings()


@lru_cache(maxsize=1)
def get_logging_settings() -> LoggingSettings:
    """获取缓存的日志配置。"""
    return LoggingSettings()


class Settings(BaseModel):
    """汇总应用、数据库、大语言模型和日志配置。"""

    app: AppSettings = Field(default_factory=get_app_settings)
    database: DatabaseSettings = Field(default_factory=get_database_settings)
    llm: LLMSettings = Field(default_factory=get_llm_settings)
    logging: LoggingSettings = Field(default_factory=get_logging_settings)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """获取缓存的完整配置。"""
    return Settings()


settings = get_settings()
app_settings = settings.app
database_settings = settings.database
llm_settings = settings.llm
logging_settings = settings.logging
