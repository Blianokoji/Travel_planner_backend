import os
import json
from typing import List
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Settings(BaseSettings):
    FIREBASE_CREDENTIALS_PATH: str
    app_name: str = "Travel Planner API"
    debug: bool = False

    # JWT settings
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY")
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24

    # API Keys
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    google_maps_api_key: str = os.getenv("GOOGLE_MAPS_API_KEY", "")

    # CORS settings
    allowed_origins: List[str] = ["*"]

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000

    # Logging
    log_level: str = "INFO"
    log_file: str = "/tmp/fastapi_app.log"

    class Config:
        env_file = ".env"
        case_sensitive = False

# Instantiate settings
settings = Settings()

# ✅ Firebase Credentials Loading
firebase_credentials_path = Path(settings.FIREBASE_CREDENTIALS_PATH).resolve()
with open(firebase_credentials_path, "r") as f:
    firebase_credentials = json.load(f)
