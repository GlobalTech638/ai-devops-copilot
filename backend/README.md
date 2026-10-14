# Backend

FastAPI service for repository analysis and AI orchestration.

## Run locally

From the `backend/` directory:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

On Windows PowerShell, activate the environment with `.venv\Scripts\Activate.ps1`.

The API docs are available at `http://127.0.0.1:8000/docs`; the liveness endpoint is `GET /health`.

## GitHub configuration

Set `GITHUB_TOKEN` in the backend environment for private repository access or live pull-request review publishing. Use a fine-grained token with the minimum required repository permissions. Never commit tokens to source control.

Set `OPENAI_API_KEY` to enable the configured OpenAI analyzer. Without it, the service uses a small deterministic fallback scanner; this is not a substitute for a full security audit.

## Pull-request review API

All routes use the `/api/v1/pull-requests` prefix and accept JSON with `repository` (for example, `owner/repo`) and `pull_request` (a positive PR number).

| Method and path | Purpose |
| --- | --- |
| `POST /review` | Return deterministic PR risk analysis |
| `POST /review/plan` | Return a review plan without posting to GitHub |
| `POST /review/publish` | Prepare a review; dry-run is the default |

Example dry-run request:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/pull-requests/review/plan \
  -H "Content-Type: application/json" \
  -d '{"repository":"owner/repo","pull_request":1}'
```

### Publishing safety

`POST /review/publish` defaults to `dry_run: true`; it returns the proposed payload and does not mutate GitHub. Live publishing requires an explicit `dry_run: false`, a `GITHUB_TOKEN`, and a `commit_id` containing the pull request head SHA when inline comments are present. Verify the repository and review payload before enabling live publishing.

The initial PR analyzer uses heuristic checks. Treat its findings as review assistance, not as a definitive security verdict or an automatic merge decision.

## Tests

From `backend/`:

```bash
PYTHONPATH=. pytest -q
```

GitHub Actions runs the backend test suite on branch pushes and pull requests targeting `main`.
