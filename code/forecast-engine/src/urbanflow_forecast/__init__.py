"""UrbanFlow forecasting package."""

from pathlib import Path

from dotenv import load_dotenv


PACKAGE_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PACKAGE_ROOT / ".env")
load_dotenv(PACKAGE_ROOT.parent / ".env")

__version__ = "0.1.0"

PREDICTION_LENGTH = 48
