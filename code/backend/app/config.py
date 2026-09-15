import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CODE_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(CODE_ROOT / ".env")
load_dotenv(PROJECT_ROOT / ".env")


MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "urbanflow")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "urbanflow_dev")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "urbanflow")

DEFAULT_DATA_DIR = CODE_ROOT / "data"
DATA_DIR = Path(os.getenv("DATA_DIR", str(DEFAULT_DATA_DIR))).resolve()

APP_LANGUAGE = os.getenv("APP_LANGUAGE", "en")
APP_TITLE = "UrbanFlow Demand Forecasting API"
APP_VERSION = "0.2.0"
APP_DESCRIPTION = "Demand forecasting and dispatch decision-support API"
API_PREFIX = "/api/v1"
API_CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "API_CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]
HEALTH_MAX_FORECAST_AGE_HOURS = int(
    os.getenv("HEALTH_MAX_FORECAST_AGE_HOURS", "24")
)
