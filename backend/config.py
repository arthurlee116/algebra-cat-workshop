from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Runtime configuration for the FastAPI service."""

    database_url: str = f"sqlite:///{Path(__file__).parent / 'data.db'}"
    ark_api_key: str | None = None
    ark_model: str = "doubao-seedream-4-0-250828"
    ark_base_url: str = "https://ark.cn-beijing.volces.com/api/v3/images/generations"
    ark_image_size: str = "2K"
    ark_response_format: str = "url"
    ark_sequential_mode: str = "disabled"
    ark_stream: bool = False
    ark_watermark: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
