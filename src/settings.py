from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

env_path = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    host: str = Field(..., alias='POSTGRES_HOST')
    port: int = Field(..., alias='POSTGRES_PORT')
    user: str = Field(..., alias='POSTGRES_USER')
    password: str = Field(..., alias='POSTGRES_PASSWORD')
    db_name: str = Field(..., alias='POSTGRES_DB')

    @property
    def database_url(self) -> str:
        return f'postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.db_name}'

    model_config = SettingsConfigDict(
        env_file=(env_path / '.env', env_path / '.env.local')
    )


settings = Settings()
