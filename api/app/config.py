import os
from functools import lru_cache
from pathlib import Path

from dotenv import dotenv_values
from pydantic_settings import BaseSettings, SettingsConfigDict

# Force-load .env even when shell already has empty values for our keys.
# Some hosts (e.g. Claude Desktop) export ANTHROPIC_API_KEY="" which would
# otherwise win over the .env file under default load_dotenv semantics.
_env_path = Path(__file__).resolve().parent.parent / ".env"
if _env_path.exists():
    for k, v in dotenv_values(str(_env_path)).items():
        if v and not os.environ.get(k):
            os.environ[k] = v


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(_env_path), extra="ignore")

    app_name: str = "AP-BidIQ API"
    environment: str = "development"

    # Defaults to local sqlite for dev; override with Neon Postgres URL in prod.
    database_url: str = "sqlite+pysqlite:///./bidiq.db"

    # Anthropic
    anthropic_api_key: str = ""
    anthropic_model_strong: str = "claude-sonnet-4-6"
    anthropic_model_fast: str = "claude-haiku-4-5"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # Path to corpus (the EPCC tender package)
    corpus_dir: str = "../data/corpus"
    synthetic_bids_dir: str = "../data/synthetic-bids"


@lru_cache
def get_settings() -> Settings:
    return Settings()
