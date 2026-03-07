from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python <3.11
    import tomli as tomllib  # type: ignore

CONFIG_ENV_VAR = "GROGBOT_CONFIG"
DEFAULT_CONFIG_PATH = Path("~/.grogbot/config.toml").expanduser()
DEFAULT_DB_PATH = Path("~/.grogbot/search.db").expanduser()


class Config(BaseModel):
    db_path: Path = Field(default=DEFAULT_DB_PATH)


def load_config(path: str | Path | None = None) -> Config:
    config_path = Path(
        os.getenv(CONFIG_ENV_VAR)
        or (str(path) if path is not None else DEFAULT_CONFIG_PATH)
    ).expanduser()
    data: dict[str, Any] = {}
    if config_path.exists():
        with config_path.open("rb") as handle:
            data = tomllib.load(handle)
    search_data = data.get("search", {}) if isinstance(data, dict) else {}
    db_path = Path(search_data.get("db_path", DEFAULT_DB_PATH)).expanduser()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return Config(db_path=db_path)
