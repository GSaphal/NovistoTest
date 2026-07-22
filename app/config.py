import os


def _env(name: str, default: str | None = None) -> str:
    value = os.environ.get(name, default)
    if value is None:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


DATA_DIR = _env("DATA_DIR", "/data")
USERS_PATH = os.path.join(DATA_DIR, "users.json")