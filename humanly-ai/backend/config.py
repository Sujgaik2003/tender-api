from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # LLM Settings (Groq/OpenAI-compatible)
    llm_api_url: str = "https://api.groq.com/openai/v1"
    llm_api_key: Optional[str] = None
    llm_model: str = "llama-3.3-70b-versatile"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
