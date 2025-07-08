import os
from pydantic import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Application settings
    app_name: str = "Travel Planner API"
    debug: bool = False
    
    # JWT settings
    jwt_secret_key: str = "Dracalar@2099"  # Change this in production
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24  # 24 hours
    
    # Database settings
    mongo_uri: str = "mongodb+srv://blessenprojects:EnBiva2qoqhsQg5u@cluster0.seoid.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    
    # API Keys
    gemini_api_key: str = ""
    google_maps_api_key: str = ""
    
    # CORS settings
    allowed_origins: List[str] = ["https://frontend-dot-weather-model-454711.el.r.appspot.com"]
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Logging settings
    log_level: str = "INFO"
    log_file: str = "/tmp/fastapi_app.log"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Create settings instance
settings = Settings()