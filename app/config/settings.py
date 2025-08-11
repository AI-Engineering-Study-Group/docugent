"""
Application settings and configuration management.
"""

from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Google ADK Configuration
    google_api_key: str = Field(..., env="GOOGLE_API_KEY")
    google_model_name: str = Field("gemini-2.5-flash", env="GOOGLE_MODEL_NAME")
    
    # Google Maps API
    google_maps_api_key: str = Field(..., env="GOOGLE_MAPS_API_KEY")
    
    # Database Configuration
    database_url: str = Field(..., env="DATABASE_URL")
    redis_url: str = Field("redis://localhost:6379/0", env="REDIS_URL")
    
    # Application Settings
    app_name: str = Field("apiconf_agent", env="APP_NAME")
    environment: str = Field("development", env="ENVIRONMENT")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    debug: bool = Field(True, env="DEBUG")
    
    # Conference Information
    conference_venue_name: str = Field(..., env="CONFERENCE_VENUE_NAME")
    conference_venue_address: str = Field(..., env="CONFERENCE_VENUE_ADDRESS")
    conference_venue_coordinates: str = Field(..., env="CONFERENCE_VENUE_COORDINATES")
    conference_dates: str = Field(..., env="CONFERENCE_DATES")
    support_phone: str = Field(..., env="SUPPORT_PHONE")
    support_email: str = Field(..., env="SUPPORT_EMAIL")
    
    # Web Scraping Settings
    scraping_delay: int = Field(1, env="SCRAPING_DELAY")
    user_agent: str = Field("Mozilla/5.0 (compatible; APIConfBot/1.0)", env="USER_AGENT")
    
    # Data Sources
    google_sheets_url: str = Field(..., env="GOOGLE_SHEETS_URL")
    
    # API Configuration
    api_host: str = Field("0.0.0.0", env="API_HOST")
    api_port: int = Field(8000, env="API_PORT")
    cors_origins: List[str] = Field(default=["http://localhost:3000"], env="CORS_ORIGINS")
    
    # Security
    secret_key: str = Field(..., env="SECRET_KEY")
    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string to list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @field_validator("conference_venue_coordinates")
    @classmethod
    def validate_coordinates(cls, v):
        """Validate venue coordinates format."""
        try:
            lat, lng = v.split(",")
            float(lat.strip())
            float(lng.strip())
            return v
        except (ValueError, AttributeError):
            raise ValueError("Coordinates must be in format 'lat,lng'")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

# Global settings instance
settings = Settings() 