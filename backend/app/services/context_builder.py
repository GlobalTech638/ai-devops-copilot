"""Build bounded, model-ready repository context from file paths and snippets."""

from dataclasses import dataclass

MAX_FILES = 80
MAX_CHARS_PER_FILE = 12_000
IGNORED_PARTS = {".git", ".venv", "venv", "node_modules", "dist", "build", "__pycache__"}


@dataclass(frozen=True)
class RepositoryFile:
    path: str
    content: str


def build_context(files: list[RepositoryFile]) -> str:
    """Create a deterministic context document with strict size bounds."""
    selected = [f for f in files if not any(part in IGNORED_PARTS for part in f.path.split("/"))][:MAX_FILES]
    sections: list[str] = []
    for file in selected:
        content = file.content[:MAX_CHARS_PER_FILE]
        sections.append(f"### FILE: {file.path}\n```\n{content}\n```")
    return "\n\n".join(sections)
