from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Post-Processing AI Quality API"
    debug: bool = False
    openai_api_key: str = ""
    huggingface_api_key: str = ""
    default_quality_threshold: float = 0.7
    default_metrics: list[str] = ["coherence", "relevance", "fluency"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
