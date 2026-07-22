import re
from dataclasses import dataclass

TERMINAL_PUNCT = (".", "?", "!", ":")

_HEADING_RE = re.compile(r"^[A-Z0-9]")
_BULLET_RE = re.compile(r"^([•\-\*]|\d+[.)])\s+")
_NUMERIC_TOKEN_RE = re.compile(r"(?<![A-Za-z])\d[\d,]*%?")



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

    return [
        Chunk(content=content, heading=heading, access=list(default_access))
        for content, heading in raw_chunks
    ]
