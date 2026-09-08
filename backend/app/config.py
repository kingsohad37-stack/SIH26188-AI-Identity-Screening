from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    supabase_url: str = "https://ocxhnbtrowgtqsgxfdly.supabase.co"
    supabase_publishable_key: str = "sb_publishable_HVG2Mt_BODr1BbGoKUZhZQ_w4HRdHQ3"
    allowed_origin: str = "http://localhost:3000"
    max_file_mb: int = 20
    model_version: str = "baseline-ocr-forensics-0.2"
    sightengine_api_user: str = ""
    sightengine_api_secret: str = ""
    sightengine_models: str = "recapture,genai"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
