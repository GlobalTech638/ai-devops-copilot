"""AI DevOps Copilot API entry point."""

from fastapi import FastAPI

app = FastAPI(
    title="AI DevOps Copilot",
    version="0.1.0",
    description="AI-powered engineering intelligence for GitHub repositories.",
)


@app.get("/health")
def health() -> dict[str, str]:
    """Return service health."""
    return {"status": "ok", "service": "ai-devops-copilot"}


@app.get("/")
def root() -> dict[str, str]:
    """Return API identity."""
    return {"name": "AI DevOps Copilot", "version": "0.1.0"}
