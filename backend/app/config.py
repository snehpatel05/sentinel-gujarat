from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    sentinel_catalogue_url: str | None = None
    sentinel_api_token: str | None = None
    sentinel_username: str | None = None
    sentinel_password: str | None = None
    sentinel_verify_tls: bool = True
    sentinel_cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    sentinel_database_url: str = "sqlite:///./data/sentinel.db"
    sentinel_use_gpu: bool = True
    sentinel_inference_sample_fps: float = 3.0
    sentinel_maptiler_key: str | None = None

    @property
    def cors_origins(self) -> list[str]:
        configured = [origin.strip() for origin in self.sentinel_cors_origins.split(",") if origin.strip()]
        required_local_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
        return list(dict.fromkeys(required_local_origins + configured))

    @property
    def live_mode(self) -> bool:
        return bool(self.sentinel_catalogue_url)


@lru_cache
def get_settings() -> Settings:
    return Settings()

