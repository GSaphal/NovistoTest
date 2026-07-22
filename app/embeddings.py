from functools import lru_cache

from openai import OpenAI

from app.config import OPENAI_API_KEY, OPENAI_EMBED_MODEL


@lru_cache(maxsize=1)
def _get_client() -> OpenAI:
    """Constructed lazily, on first real use, rather than at import time --
    otherwise importing this module at all requires a real API key to be
    set, even in tests that never call the network."""
    return OpenAI(api_key=OPENAI_API_KEY)


def embed_batch(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    resp = _get_client().embeddings.create(model=OPENAI_EMBED_MODEL, input=texts)
    return [d.embedding for d in resp.data]


def embed_one(text: str) -> list[float]:
    return embed_batch([text])[0]