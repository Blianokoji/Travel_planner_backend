import os
import json
from typing import List
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Firebase settings - use environment variable for credentials
    FIREBASE_CREDENTIALS_PATH: str = ""
    
    app_name: str = "Travel Planner API"
    debug: bool = False

    # JWT settings
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24

    # API Keys
    gemini_api_key: str = ""
    google_maps_api_key: str = ""

    # CORS settings
    allowed_origins: List[str] = []

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000

    # Logging
    log_level: str = "INFO"
    log_file: str = "/tmp/fastapi_app.log"

    class Config:
        case_sensitive = False


# Instantiate settings
settings = Settings()

# Firebase Credentials Loading
firebase_credentials = None

if settings.FIREBASE_CREDENTIALS_PATH:
    # Load from file path
    try:
        firebase_credentials_path = Path(settings.FIREBASE_CREDENTIALS_PATH).resolve()
        with open(firebase_credentials_path, "r") as f:
            firebase_credentials = json.load(f)
    except Exception as e:
        print(f"Error loading Firebase credentials from file: {e}")
else:
    print("Warning: No Firebase credentials provided. Set FIREBASE_CREDENTIALS_PATH")
