"""AI DevOps Copilot API entry point."""

from fastapi import FastAPI

from app.api.ai import router as ai_router
from app.api.analyze import router as analyze_router
from app.api.health import router as health_router

app = FastAPI(
    title="AI DevOps Copilot",
    version="0.1.0",
    description="AI-powered engineering intelligence for GitHub repositories.",
)

app.include_router(analyze_router)
app.include_router(health_router)
app.include_router(ai_router)


@app.get("/health")
def health() -> dict[str, str]:
    """Return service health."""
    return {"status": "ok", "service": "ai-devops-copilot"}


@app.get("/")
def root() -> dict[str, str]:
    """Return API identity."""
    return {"name": "AI DevOps Copilot", "version": "0.1.0"}
