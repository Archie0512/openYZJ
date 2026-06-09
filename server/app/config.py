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

    # 云之家机器人推送地址
    yunzhijia_webhook_url: str = "https://www.yunzhijia.com/gateway/robot/webhook/send?yzjtype=12&yzjtoken=e9bab73727104e15b92c7f93254f7bc4"

    # 金斗云道闸 API 配置
    mys4s_secret_key: str = "085790cd17bc418c84d573aa044a0bb8"
    mys4s_api_key: str = "baode"
    mys4s_base_url: str = "https://mys4s.cn/grey/openapi"  # 测试环境；生产环境去掉 /grey

    # 运行环境
    env: str = "dev"
    log_level: str = "INFO"

    # 对外访问域名
    base_url: str = "https://ibowdex.cn"

    # 出门单 PNG 存储目录
    passes_dir: str = "static/passes"

    # 卡片消息模板 ID（云之家平台注册的模板）
    mys4s_card_template_id: str = "6a278658e4b0432247a2fa40"

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
