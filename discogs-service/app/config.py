from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    discogs_key: str
    discogs_secret: str
    discogs_user_agent: str
    discogs_api_base_url: str = "https://api.discogs.com"
    discogs_oauth_token: str = ""
    discogs_oauth_token_secret: str = ""
    log_level: str = "INFO"
    discogs_rate_limit_per_minute: int = 55
    discogs_import_log_level: str = "INFO"
    system_log_url: str = "http://api:8000"
    system_log_token: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
