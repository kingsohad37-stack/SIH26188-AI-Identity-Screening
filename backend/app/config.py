from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    supabase_url: str
    supabase_service_role_key: str
    allowed_origin: str = "http://localhost:3000"
    max_file_mb: int = 20
    model_version: str = "baseline-ocr-forensics-0.1"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
