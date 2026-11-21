from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Локальный llama-cpp server на 127.0.0.1:8080 без пароля
    openai_api_key: str = "no-key"
    openai_base_url: str = "http://127.0.0.1:8080/v1"
    model_id: str = "local-model"
    provider_name: str = "llama-cpp"

    # Соответствующий тарифный снимок OpenRouter (USD за 1M токенов, P_in <= 0.10)
    openrouter_model_id: str = "qwen/qwen-2.5-7b-instruct"
    input_price_per_1m: float = 0.05
    output_price_per_1m: float = 0.10

    llm_timeout_seconds: float = 600.0
    kb_dir: Path = Path("../data/kb")
    db_path: Path = Path("./data/synonyx.db")


settings = Settings()
