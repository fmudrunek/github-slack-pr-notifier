from datetime import datetime, timezone

from notifier.repository import PullRequestInfo, RepositoryInfo
from notifier.summary_formatter import SummaryMessageFormatter

formatter = SummaryMessageFormatter()


def _make_pr(
    name: str = "Test PR",
    author: str = "alice",
    age: tuple[int, int] = (0, 1),
    review_status: str = "WAITING",
    additions: int = 10,
    deletions: int = 5,
    changed_files: int = 2,
    copilot_requester: str | None = None,
) -> PullRequestInfo:
    return PullRequestInfo(
        name=name,
        author=author,
        created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        age=age,
        review_status=review_status,
        url="https://github.com/org/repo/pull/1",
        additions=additions,
        deletions=deletions,
        changed_files=changed_files,
        copilot_requester=copilot_requester,
    )


def _extract_text(messages: list) -> str:
    """Flatten all text content from block kit messages into a single string for easy assertions."""
    import json
    return json.dumps(messages)


# Age urgency tests
def test_age_urgency_none_at_3_days() -> None:
    pr = _make_pr(age=(3, 0))
    repo = RepositoryInfo(name="org/repo", pulls=[pr])
    text = _extract_text(formatter.get_messages_for_repo(repo))
    assert '"name": "alert"' not in text
    assert '"name": "warning"' not in text


def test_age_urgency_warning_at_5_days() -> None:
    pr = _make_pr(age=(5, 0))
    repo = RepositoryInfo(name="org/repo", pulls=[pr])
    text = _extract_text(formatter.get_messages_for_repo(repo))
    assert '"name": "warning"' in text


def test_age_urgency_alert_at_10_days() -> None:
    pr = _make_pr(age=(10, 0))
    repo = RepositoryInfo(name="org/repo", pulls=[pr])
    text = _extract_text(formatter.get_messages_for_repo(repo))
    assert '"name": "alert"' in text


# Day rounding test
def test_day_rounding_2d_13h_becomes_3_days() -> None:
    pr = _make_pr(age=(2, 13))
    repo = RepositoryInfo(name="org/repo", pulls=[pr])
    text = _extract_text(formatter.get_messages_for_repo(repo))
    assert "3 days" in text


def test_day_rounding_2d_11h_stays_2_days() -> None:
    pr = _make_pr(age=(2, 11))
    repo = RepositoryInfo(name="org/repo", pulls=[pr])
    text = _extract_text(formatter.get_messages_for_repo(repo))
    assert "2 days" in text


# Hours display for sub-day age
def test_hours_display_for_0_days() -> None:
    pr = _make_pr(age=(0, 5))
    repo = RepositoryInfo(name="org/repo", pulls=[pr])
    text = _extract_text(formatter.get_messages_for_repo(repo))
    assert "5 hours" in text


# File pluralization tests
def test_file_singular() -> None:
    pr = _make_pr(changed_files=1)
    repo = RepositoryInfo(name="org/repo", pulls=[pr])
    text = _extract_text(formatter.get_messages_for_repo(repo))
    assert "1 file" in text
    assert "1 files" not in text


def test_file_plural() -> None:
    pr = _make_pr(changed_files=2)
    repo = RepositoryInfo(name="org/repo", pulls=[pr])
    text = _extract_text(formatter.get_messages_for_repo(repo))
    assert "2 files" in text


# Review status tests
def test_review_status_approved_shown() -> None:
    pr = _make_pr(review_status="APPROVED")
    repo = RepositoryInfo(name="org/repo", pulls=[pr])
    text = _extract_text(formatter.get_messages_for_repo(repo))
    assert "APPROVED" in text


def test_review_status_waiting_hidden() -> None:
    pr = _make_pr(review_status="WAITING")
    repo = RepositoryInfo(name="org/repo", pulls=[pr])
    text = _extract_text(formatter.get_messages_for_repo(repo))
    assert "WAITING" not in text


def test_review_status_changes_requested_shown() -> None:
    pr = _make_pr(review_status="CHANGES_REQUESTED")
    repo = RepositoryInfo(name="org/repo", pulls=[pr])
    text = _extract_text(formatter.get_messages_for_repo(repo))
    assert "CHANGES_REQUESTED" in text


# Repository header test
def test_repo_header_on_first_pr_only() -> None:
    pr1 = _make_pr(name="PR 1")
    pr2 = _make_pr(name="PR 2")
    repo = RepositoryInfo(name="org/repo", pulls=[pr1, pr2])
    messages = formatter.get_messages_for_repo(repo)
    assert len(messages) == 2
    # First message has header + PR block
    assert len(messages[0]) == 2
    assert messages[0][0]["type"] == "header"
    # Second message has only PR block
    assert len(messages[1]) == 1


# Copilot attribution
def test_author_shown_plain_when_no_copilot_requester() -> None:
    pr = _make_pr(author="alice")
    repo = RepositoryInfo(name="org/repo", pulls=[pr])
    text = _extract_text(formatter.get_messages_for_repo(repo))
    assert "by alice" in text
    assert "via Copilot" not in text


def test_author_shown_as_via_copilot_when_requester_set() -> None:
    pr = _make_pr(author="Copilot", copilot_requester="test-author")
    repo = RepositoryInfo(name="org/repo", pulls=[pr])
    text = _extract_text(formatter.get_messages_for_repo(repo))
    assert "by test-author (via Copilot)" in text


# Empty pulls
def test_empty_pulls_returns_no_messages() -> None:
    repo = RepositoryInfo(name="org/repo", pulls=[])
    messages = formatter.get_messages_for_repo(repo)
    assert messages == []
