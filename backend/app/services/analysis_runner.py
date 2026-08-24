"""Repository analysis orchestration boundary."""

from app.models.findings import AnalysisResult
from app.services.ai_analyzer import baseline_analysis
from app.services.context_builder import RepositoryFile, build_context
from app.services.github_adapter import GitHubRepositoryClient
from app.services.github_ingestion import select_files


def run_repository_analysis(
    client: GitHubRepositoryClient,
    repository: str,
    ref: str = "main",
) -> AnalysisResult:
    """Build bounded repository context and execute the current analyzer."""
    entries = select_files(client.list_tree(repository, ref))
    files: list[RepositoryFile] = []
    for entry in entries:
        item = client.get_file(repository, entry["path"], ref)
        files.append(RepositoryFile(path=item.path, content=item.content))
    return baseline_analysis(build_context(files))
