from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[2]
LOCAL_DATA = BASE_DIR / "local_data"
BRONZE_DIR = LOCAL_DATA / "bronze"
SILVER_DIR = LOCAL_DATA / "silver"
GOLD_DIR = LOCAL_DATA / "gold"
ENRICHED_DIR = LOCAL_DATA / "enriched"


@dataclass(frozen=True)
class Settings:
    public_api_base_url: str = os.getenv("PUBLIC_API_BASE_URL", "https://api.open-meteo.com/v1")
    geocoding_api_base_url: str = os.getenv("GEOCODING_API_BASE_URL", "https://geocoding-api.open-meteo.com/v1")
    target_cities: list[str] = field(
        default_factory=lambda: [
            city.strip()
            for city in os.getenv("TARGET_CITIES", "Buenos Aires,Cordoba,Rosario").split(",")
            if city.strip()
        ]
    )
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    openrouter_model: str = os.getenv("OPENROUTER_MODEL", "google/gemma-3-4b-it:free")


settings = Settings()
