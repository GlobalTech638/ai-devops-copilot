"""Repository manifest extraction helpers."""

from dataclasses import dataclass
from pathlib import PurePosixPath

IGNORED = {".git", ".venv", "venv", "node_modules", "dist", "build", "__pycache__"}
IMPORTANT = {
    "README.md", "pyproject.toml", "requirements.txt", "package.json",
    "Dockerfile", "docker-compose.yml", "go.mod", "Cargo.toml",
}


@dataclass(frozen=True)
class RepositoryManifest:
    files: list[str]
    important_files: list[str]


def build_manifest(paths: list[str]) -> RepositoryManifest:
    """Normalize paths and identify high-value context files."""
    clean = sorted({str(PurePosixPath(p)) for p in paths if p and not any(x in p.split("/") for x in IGNORED)})
    important = [path for path in clean if PurePosixPath(path).name in IMPORTANT]
    return RepositoryManifest(files=clean, important_files=important)
