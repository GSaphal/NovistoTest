import re
from dataclasses import dataclass

TERMINAL_PUNCT = (".", "?", "!", ":")

_HEADING_RE = re.compile(r"^[A-Z0-9]")
_BULLET_RE = re.compile(r"^([•\-\*]|\d+[.)])\s+")
_NUMERIC_TOKEN_RE = re.compile(r"(?<![A-Za-z])\d[\d,]*%?")
_TRIGGER_RE = re.compile(r"CONFIDENTIAL", re.IGNORECASE)
_BANNER_WINDOW = 150
PROPAGATE_CHUNKS = 1

_ROLE_PATTERNS = {
    "exec": re.compile(r"\bEXEC(?:UTIVE)?(?:\s+COMMITTEE)?\b", re.IGNORECASE),
    "finance": re.compile(r"\bFINANCE\b", re.IGNORECASE),
    "people": re.compile(r"\b(PEOPLE|HR|HUMAN\s+RESOURCES)\b", re.IGNORECASE),
    "sales": re.compile(r"\bSALES\b", re.IGNORECASE),
    "marketing": re.compile(r"\bMARKETING\b", re.IGNORECASE),
    "ops": re.compile(r"\b(OPS|OPERATIONS)\b", re.IGNORECASE),
}

@dataclass
class Chunk:
    content: str
    heading: str | None
    access: list[str]
    restricted_override: bool = False


def _is_heading(line: str) -> bool:
    words = line.split()
    return (
        1 <= len(words) <= 8
        and line[-1] not in ".?!,;:"
        and not _BULLET_RE.match(line)
        and bool(_HEADING_RE.match(line))
        and len(_NUMERIC_TOKEN_RE.findall(line)) < 2 
    )

def _is_bullet(line: str) -> bool:
    return bool(_BULLET_RE.match(line))

def detect_banner_roles(text: str) -> set[str] | None:
    trigger = _TRIGGER_RE.search(text)
    if not trigger:
        return None
    window = text[trigger.start() : trigger.start() + _BANNER_WINDOW]
    roles = {role for role, pattern in _ROLE_PATTERNS.items() if pattern.search(window)}
    return roles or None

def _to_units(text: str) -> list[str]:
    """Merge wrapped PDF lines into logical paragraph/bullet/heading units."""
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    units: list[str] = []
    buf = ""
    for line in lines:
        if _is_heading(line) or _is_bullet(line):
            if buf:
                units.append(buf.strip())
                buf = ""
            units.append(line)
            continue
        if buf and buf.rstrip()[-1] not in TERMINAL_PUNCT:
            buf = f"{buf} {line}"
        else:
            if buf:
                units.append(buf.strip())
            buf = line
    if buf:
        units.append(buf.strip())
    return units

def chunk_document(text: str, default_access: list[str]) -> list[Chunk]:
    units = _to_units(text)

    raw_chunks: list[tuple[str, str | None]] = []
    current_heading: str | None = None
    for unit in units:
        if _is_heading(unit) and not _is_bullet(unit):
            current_heading = unit
            continue
        raw_chunks.append((unit, current_heading))

    chunks = [
        Chunk(content=content, heading=heading, access=list(default_access))
        for content, heading in raw_chunks
    ]

    for i, chunk in enumerate(chunks):
        banner_roles = detect_banner_roles(chunk.content)
        if banner_roles is None or not banner_roles < set(chunk.access):
            continue
        narrowed = sorted(banner_roles)
        for j in range(i, min(i + 1 + PROPAGATE_CHUNKS, len(chunks))):
            chunks[j].access = list(narrowed)
            chunks[j].restricted_override = True

    return chunks
