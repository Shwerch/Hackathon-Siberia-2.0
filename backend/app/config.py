from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_base_url: str = "http://127.0.0.1:8080/v1"
    llm_api_key: str = ""
    llm_model_id: str = "local-model"
    llm_provider: str = "Local"
    llm_openrouter_url: str = "https://openrouter.ai/models"
    llm_p_input_usd_per_1m: float = 0.10
    llm_p_output_usd_per_1m: float = 0.40
    llm_timeout_seconds: float = 60.0
    llm_use_response_format: bool = False

    db_path: str = "/app/data/synonyx.db"
    kb_dir: str = "/app/synonyx_base"
    schema_version: str = "1.0"


settings = Settings()
