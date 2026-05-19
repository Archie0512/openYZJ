"""应用全局配置：基于 pydantic-settings v2 从 .env 读取。"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # MongoDB 连接配置
    mongo_user: str
    mongo_password: str
    mongo_host: str = "mongo"
    mongo_port: int = 27017
    mongo_db: str = "yunzhijia"

    # 应用密钥
    app_secret_key: str
    admin_token: str

    # 可选：OpenAI 兼容接口（用于 ai_handler）
    openai_api_base: str = "https://api.openai.com/v1"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # 运行环境
    env: str = "dev"
    log_level: str = "INFO"

    @property
    def mongo_uri(self) -> str:
        """构造 MongoDB 连接 URI（使用 admin 库进行身份验证）。"""
        return (
            f"mongodb://{self.mongo_user}:{self.mongo_password}"
            f"@{self.mongo_host}:{self.mongo_port}/?authSource=admin"
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


# 全局单例配置
settings = Settings()
