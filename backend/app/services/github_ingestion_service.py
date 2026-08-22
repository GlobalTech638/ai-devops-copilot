"""Service layer for turning GitHub tree metadata into analysis inputs."""

from dataclasses import dataclass

from app.services.github_ingestion import select_files


@dataclass(frozen=True)
class RepositorySnapshot:
    repository: str
    ref: str
    files: list[dict]


def build_snapshot(repository: str, ref: str, tree_entries: list[dict]) -> RepositorySnapshot:
    """Build a bounded snapshot from GitHub tree entries.

    Network access is intentionally kept outside this function so the service is
    deterministic and easy to test. A GitHub adapter can supply the tree entries.
    """
    return RepositorySnapshot(
        repository=repository,
        ref=ref,
        files=select_files(tree_entries),
    )
