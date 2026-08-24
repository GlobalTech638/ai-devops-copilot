"""Provider interface for GitHub repository access.

The adapter is intentionally isolated from analysis logic. A production
implementation can inject a GitHub token/app client without changing the
analyzer, context builder, or scoring code.
"""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class GitHubFile:
    path: str
    size: int
    content: str


class GitHubRepositoryClient(Protocol):
    def list_tree(self, repository: str, ref: str) -> list[dict]:
        """Return repository tree entries for a ref."""

    def get_file(self, repository: str, path: str, ref: str) -> GitHubFile:
        """Return one repository file."""
