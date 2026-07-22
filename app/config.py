import os
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent


def _env(name: str, default: str | None = None) -> str:
    value = os.environ.get(name, default)
    if value is None:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


DATA_DIR = _env("DATA_DIR", str(_REPO_ROOT / "data"))
USERS_PATH = os.path.join(DATA_DIR, "users.json")