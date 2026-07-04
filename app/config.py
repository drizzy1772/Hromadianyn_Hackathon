from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):

    database_url: str = "postgresql://user:password@localhost:5432/hromadianyn_db"

    geocoder_user_agent: str = "hromadianyn_fop_app"
    geocoder_rate_limit_sec: float = 1.0 

    vkursi_url: str = ""

    ukrsib_branches_url: str = "https://my.ukrsibbank.com/ua/personal/branch/"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()
