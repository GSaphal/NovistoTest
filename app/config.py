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
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_EMBED_MODEL = _env("OPENAI_EMBED_MODEL", "text-embedding-3-small")
DATABASE_URL = _env("DATABASE_URL", "postgresql://rag:rag@db:5432/rag")
EMBED_DIM = int(_env("EMBED_DIM", "1536"))