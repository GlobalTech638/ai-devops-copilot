"""Run a repository analysis job from GitHub through the analyzer boundary."""

from app.models.jobs import JobStatus
from app.services.analyzer_factory import get_analyzer
from app.services.github_api_client import GitHubApiClient
from app.services.github_ingestion import select_files
from app.services.job_store import fail_job, save_result, update_job


def run_analysis(job_id: str, repository: str, ref: str) -> None:
    """Fetch a bounded GitHub snapshot, analyze it, and persist the result."""
    try:
        update_job(job_id, JobStatus.SCANNING, 10)
        github = GitHubApiClient()
        tree = github.list_tree(repository, ref)

        selected = select_files(tree)
        update_job(job_id, JobStatus.INDEXING, 35)

        chunks: list[str] = []
        total = len(selected)
        for index, entry in enumerate(selected):
            file = github.get_file(repository, entry["path"], ref)
            chunks.append(f"FILE: {file.path}\n{file.content}")
            progress = 35 + int(((index + 1) / max(total, 1)) * 25)
            update_job(job_id, JobStatus.INDEXING, min(progress, 60))

        update_job(job_id, JobStatus.ANALYZING, 70)
        context = "\n\n".join(chunks)
        result = get_analyzer().analyze(context)
        save_result(job_id, result)
    except Exception as exc:
        fail_job(job_id, str(exc))
