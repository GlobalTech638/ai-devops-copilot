"""Safe GitHub repository ingestion primitives."""

from dataclasses import dataclass
from pathlib import PurePosixPath

MAX_FILES = 80
MAX_FILE_BYTES = 200_000
IGNORED_DIRS = {".git", ".venv", "venv", "node_modules", "dist", "build", "__pycache__", ".next"}
BINARY_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".zip", ".gz", ".woff", ".woff2", ".mp4", ".mp3"}
SECRET_NAMES = {".env", ".env.local", ".env.production", "id_rsa", "id_ed25519"}


@dataclass(frozen=True)
class IngestedFile:
    path: str
    content: str


def is_safe_path(path: str) -> bool:
    """Reject traversal and absolute paths before processing repository data."""
    normalized = PurePosixPath(path)
    return not normalized.is_absolute() and ".." not in normalized.parts


def should_ingest(path: str, size: int) -> bool:
    """Return whether a repository file is suitable for semantic analysis."""
    if not is_safe_path(path) or size > MAX_FILE_BYTES:
        return False
    parts = PurePosixPath(path).parts
    if any(part in IGNORED_DIRS for part in parts):
        return False
    name = PurePosixPath(path).name
    if name in SECRET_NAMES:
        return False
    return PurePosixPath(path).suffix.lower() not in BINARY_EXTENSIONS


def select_files(entries: list[dict]) -> list[dict]:
    """Filter and bound GitHub tree entries before content retrieval."""
    selected = [
        entry for entry in entries
        if entry.get("type") == "blob"
        and should_ingest(entry.get("path", ""), int(entry.get("size", 0)))
    ]
    return selected[:MAX_FILES]
