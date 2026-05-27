from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongo_uri: str
    mongo_uri_test: str
    mongo_db: str
    mongo_db_test: str

    app_env: str = "development"
    debug: bool = False
    timezone: str = "UTC"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()
