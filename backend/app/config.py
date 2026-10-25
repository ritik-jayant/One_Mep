from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]
BACKEND = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND / ".env", extra="ignore")

    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o"
    llm_fast_model: str = "gpt-4o-mini"
    database_url: str = f"sqlite:///{(ROOT / 'data' / 'app.db').as_posix()}"
    cors_origins: str = "http://localhost:5173"
    upload_dir: Path = ROOT / "data" / "uploads"
    output_dir: Path = ROOT / "data" / "outputs"


settings = Settings()
settings.upload_dir.mkdir(parents=True, exist_ok=True)
settings.output_dir.mkdir(parents=True, exist_ok=True)
(ROOT / "data").mkdir(parents=True, exist_ok=True)
