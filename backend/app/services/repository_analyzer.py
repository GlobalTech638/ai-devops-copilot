"""Deterministic repository analysis primitives.

The MVP deliberately starts with deterministic signals. AI reasoning will consume
these structured findings instead of receiving an unbounded repository dump.
"""

from dataclasses import dataclass
from pathlib import PurePosixPath


@dataclass(frozen=True)
class RepositoryFinding:
    category: str
    severity: str
    message: str


IGNORED = {".git", ".venv", "node_modules", "dist", "build", "__pycache__"}


def analyze_paths(paths: list[str]) -> list[RepositoryFinding]:
    """Infer basic technology and repository hygiene signals from file paths."""
    normalized = [PurePosixPath(path) for path in paths]
    names = {path.name for path in normalized}
    findings: list[RepositoryFinding] = []

    if "package.json" in names:
        findings.append(RepositoryFinding("technology", "info", "JavaScript/TypeScript project detected."))
    if "pyproject.toml" in names or "requirements.txt" in names:
        findings.append(RepositoryFinding("technology", "info", "Python project detected."))
    if "Dockerfile" in names or "docker-compose.yml" in names:
        findings.append(RepositoryFinding("infrastructure", "info", "Container tooling detected."))
    if not any(name in names for name in {"README.md", "README.rst", "README.txt"}):
        findings.append(RepositoryFinding("documentation", "low", "Repository does not contain a README."))
    if not any(path.parts[-1] in {"test", "tests", "spec", "__tests__"} for path in normalized):
        findings.append(RepositoryFinding("testing", "medium", "No obvious test directory was detected."))

    return findings
