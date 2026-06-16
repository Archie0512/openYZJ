"""代理网关独立配置：基于 pydantic-settings v2 从 .env 读取。"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # MongoDB 连接配置（与主服务共享同一 MongoDB 实例）
    mongo_user: str
    mongo_password: str
    mongo_host: str = "mongo"
    mongo_port: int = 27017
    mongo_db: str = "yunzhijia"

    # 应用密钥（用于 Fernet 加密 proxy client secrets）
    app_secret_key: str

    # Admin 管理接口 Token
    admin_token: str

    # 运行环境
    env: str = "dev"
    log_level: str = "INFO"

    # ── 金蝶发票云代理配置 ──────────────────────────
    kdcloud_test_base_url: str = "https://baode.test.kdcloud.com"
    kdcloud_prod_base_url: str = "https://baode.kdcloud.com"
    kdcloud_app_id: str = ""
    kdcloud_app_secret: str = ""
    kdcloud_user: str = ""
    kdcloud_account_id: str = ""
    kdcloud_language: str = "en"
    kdcloud_usertype: str = "UserName"

    # ── 金蝶统一网关配置 ──────────────────────────
    kdcloud_business_system_code: str = ""
    kdcloud_aes_key: str = ""

    # ── 代理网关开关与限额 ──────────────────────────
    proxy_api_enabled: bool = True  # 独立容器始终启用
    proxy_rate_limit_default: int = 60
    proxy_token_refresh_margin: int = 600
    proxy_max_body_size_mb: int = 10

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
