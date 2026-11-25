"""使用 Pydantic Settings 统一加载和校验应用配置。"""

from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field, PostgresDsn, SecretStr
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
    """数据库连接配置。"""

    db_host: str = Field(default="localhost", alias="DB_HOST")
    db_port: int = Field(default=5432, ge=1, le=65535, alias="DB_PORT")
    db_name: str = Field(default="agent_service", alias="DB_NAME")
    db_user: str = Field(default="postgres", alias="DB_USER")
    db_password: SecretStr = Field(default="", alias="DB_PASSWORD")

    def get_database_url(self) -> str:
        """根据配置生成 PostgreSQL 连接 URL。"""
        return str(
            PostgresDsn.build(
                scheme="postgresql",
                username=self.db_user,
                password=self.db_password.get_secret_value(),
                host=self.db_host,
                port=self.db_port,
                path=self.db_name,
            )
        )


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
