import pytest

from app.services.review_plan import ReviewComment, ReviewPlan
from app.services.review_publisher import ReviewPublishError, publish_review


def sample_plan():
    return ReviewPlan(
        recommendation="REQUEST_CHANGES",
        comments=[
            ReviewComment(
                path="app/config.py",
                line=12,
                side="RIGHT",
                severity="critical",
                body="Possible credential introduced.",
                confidence=0.94,
            )
        ],
    )


def test_publish_review_defaults_to_dry_run():
    result = publish_review("owner/repo", 7, sample_plan())

    assert result["dry_run"] is True
    assert result["payload"]["action"] == "REQUEST_CHANGES"
    assert result["payload"]["comments"][0]["path"] == "app/config.py"
    assert result["payload"]["comments"][0]["line"] == 12


def test_live_inline_review_requires_commit_sha():
    with pytest.raises(ReviewPublishError, match="commit_id"):
        publish_review("owner/repo", 7, sample_plan(), dry_run=False)
