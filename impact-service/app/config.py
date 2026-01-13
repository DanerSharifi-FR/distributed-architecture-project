from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    app_name: str = "Impact Service"
    mongo_url: str = "mongodb://mongo:27017"
    mongo_db: str = "impact_db"
    flight_service_url: str = "http://flight-service:5000"
    weather_service_url: str = "http://weather-service:8001"
    satellite_service_url: str = "http://satellite-service:8080"
    use_mock_weather: bool = True
    use_mock_satellite: bool = True
    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings:
    return Settings()
