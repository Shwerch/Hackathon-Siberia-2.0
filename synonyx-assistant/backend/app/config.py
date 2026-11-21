from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openai_api_key: str = "sk-local-or-openrouter"
    openai_base_url: str = "http://localhost:8080/v1"
    model_id: str = "ThinkingCap-Qwen3.8-27B-RCO-4.2bpw.gguf"
    provider_name: str = "custom-openai-compatible"

    openrouter_model_id: str = "qwen/qwen3.8-27b"
    input_price_per_1m: float = 0.035
    output_price_per_1m: float = 1.5

    llm_timeout_seconds: float = 15.0
    kb_dir: Path = Path("../data/kb")
    db_path: Path = Path("./data/synonyx.db")


settings = Settings()
