import json
from pathlib import Path
from typing import Optional
from dataclasses import asdict
from src.models import ParserConfig

CONFIG_PATH = Path(__file__).parent / "last_run.json"


def save_last_config(cfg: ParserConfig) -> None:
    with CONFIG_PATH.open("w", encoding="utf-8") as f:
        json.dump(asdict(cfg), f, ensure_ascii=False, indent=2)


def load_last_config() -> Optional[ParserConfig]:
    if not CONFIG_PATH.exists():
        return None

    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
            return ParserConfig(**data)
    except Exception:
        return None



