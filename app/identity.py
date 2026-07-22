import json
from dataclasses import dataclass
from functools import lru_cache

from app.config import USERS_PATH


@dataclass(frozen=True)
class User:
    id: str
    name: str
    roles: tuple[str, ...]


class AuthError(Exception):
    pass


def load_users(path: str) -> dict[str, User]:
    """Load users.json into a token -> User lookup. Takes an explicit path
    (rather than reading a module-level config constant directly) so tests
    can point it at a fixture file instead of the real one."""
    with open(path) as f:
        raw = json.load(f)
    return {
        u["token"]: User(id=u["id"], name=u["name"], roles=tuple(u["roles"]))
        for u in raw["users"]
    }


def resolve_token(token: str, users_by_token: dict[str, User]) -> User:
    """Resolve a bearer-style demo token to a user + their roles. This is
    the only identity check in the system -- every MCP tool call goes
    through this before touching the retrieval layer."""
    if not token:
        raise AuthError("Missing token")
    user = users_by_token.get(token)
    if user is None:
        raise AuthError("Invalid token")
    return user


@lru_cache(maxsize=1)
def get_users_by_token() -> dict[str, User]:
    """Production entry point: lazily loads once from the real users.json
    path and caches it. Nothing else in the codebase should read
    users.json directly -- callers use this; tests use load_users() with
    a fixture path and never touch this cached singleton at all."""
    return load_users(USERS_PATH)