"""
Application settings — all values can be overridden via environment variables
or a .env file (loaded automatically by pydantic-settings).
"""
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── App ───────────────────────────────────────────────────────────────────
    project_name: str = "Post-Processing AI Quality API"
    version: str = "0.1.0"
    debug: bool = False

    # ── Embedding model (used by coherence/fluency/relevance scorers) ─────────
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # ── OpenAI ───────────────────────────────────────────────────────────────
    openai_api_key: Optional[str] = None
    openai_default_model: str = "gpt-4o-mini"

    # ── Anthropic ─────────────────────────────────────────────────────────────
    anthropic_api_key: Optional[str] = None
    anthropic_default_model: str = "claude-3-haiku-20240307"

    # ── HuggingFace ───────────────────────────────────────────────────────────
    huggingface_api_key: Optional[str] = None
    huggingface_default_model: str = "mistralai/Mistral-7B-Instruct-v0.2"

    # ── Provider call settings ─────────────────────────────────────────────────
    provider_timeout_seconds: float = 30.0
    provider_max_retries: int = 2


settings = Settings()
