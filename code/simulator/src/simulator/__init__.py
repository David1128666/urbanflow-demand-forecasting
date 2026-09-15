"""UrbanFlow virtual data simulator package."""

from pathlib import Path

from dotenv import load_dotenv


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PACKAGE_ROOT / ".env")
load_dotenv(PACKAGE_ROOT.parent / ".env")

__version__ = "0.1.0"

from simulator.config import SimulationConfig
from simulator.generator import GenerationResult, generate_dataset

__all__ = [
    "GenerationResult",
    "SimulationConfig",
    "generate_dataset",
]
