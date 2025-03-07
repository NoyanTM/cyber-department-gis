import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(".env"))

BASE_DIR = Path(__file__).parent.parent.parent
# CWD_DIR = Path.cwd()


@dataclass
class Config:
    EARTHENGINE_TOKEN: dict
    EGISTIC_CLIENT_USERNAME: str
    EGISTIC_CLIENT_PASSWORD: str


@lru_cache
def load_config() -> Config:
    return Config(
        EARTHENGINE_TOKEN=os.environ.get("EARTHENGINE_TOKEN"),
        EGISTIC_CLIENT_USERNAME=os.environ.get("EGISTIC_CLIENT_USERNAME"),
        EGISTIC_CLIENT_PASSWORD=os.environ.get("EGISTIC_CLIENT_PASSWORD"),
    )
