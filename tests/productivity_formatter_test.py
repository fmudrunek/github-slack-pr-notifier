import json

from notifier.repository import RepositoryProductivityMetrics, TeamProductivityMetrics
from notifier.productivity_formatter import ProductivityMessageFormatter

formatter = ProductivityMessageFormatter()


def _make_metrics(
    time_window_days: int = 14,
    total_merged_prs: int = 5,
    total_lines_added: int = 100,
    total_lines_deleted: int = 50,
    repository_breakdown: list[RepositoryProductivityMetrics] | None = None,
    reviewer_approvals: dict[str, int] | None = None,
) -> TeamProductivityMetrics:
    return TeamProductivityMetrics(
        time_window_days=time_window_days,
        total_merged_prs=total_merged_prs,
        total_lines_added=total_lines_added,
        total_lines_deleted=total_lines_deleted,
        repository_breakdown=repository_breakdown or [],
        reviewer_approvals=reviewer_approvals or {},
    )


def _extract_text(messages: list) -> str:
    return json.dumps(messages)


# Empty metrics
def test_empty_metrics_no_prs() -> None:
    metrics = _make_metrics(total_merged_prs=0, reviewer_approvals={})
    text = _extract_text(formatter.get_messages_for_team_metrics(metrics))
    assert "*0*" in text  # 0 merged PRs shown


def test_empty_metrics_no_reviewers() -> None:
    metrics = _make_metrics(reviewer_approvals={})
    text = _extract_text(formatter.get_messages_for_team_metrics(metrics))
    # No reviewer section when empty
    assert "Top Reviewers" not in text


# Activity emojis
def test_activity_emoji_diamond_for_1_pr() -> None:
    repo = RepositoryProductivityMetrics(repository_name="org/small-repo", merged_prs_count=1, lines_added=10, lines_deleted=5)
    metrics = _make_metrics(repository_breakdown=[repo])
    text = _extract_text(formatter.get_messages_for_team_metrics(metrics))
    assert ":small_blue_diamond:" in text


def test_activity_emoji_zap_for_2_prs() -> None:
    repo = RepositoryProductivityMetrics(repository_name="org/medium-repo", merged_prs_count=2, lines_added=50, lines_deleted=10)
    metrics = _make_metrics(repository_breakdown=[repo])
    text = _extract_text(formatter.get_messages_for_team_metrics(metrics))
    assert ":zap:" in text


def test_activity_emoji_fire_for_5_prs() -> None:
    repo = RepositoryProductivityMetrics(repository_name="org/hot-repo", merged_prs_count=5, lines_added=500, lines_deleted=100)
    metrics = _make_metrics(repository_breakdown=[repo])
    text = _extract_text(formatter.get_messages_for_team_metrics(metrics))
    assert ":fire:" in text


# Repo name display strips org prefix
def test_repo_display_strips_org_prefix() -> None:
    repo = RepositoryProductivityMetrics(repository_name="org/my-repo", merged_prs_count=1, lines_added=10, lines_deleted=5)
    metrics = _make_metrics(repository_breakdown=[repo])
    text = _extract_text(formatter.get_messages_for_team_metrics(metrics))
    assert "*my-repo*" in text


# No active repos
def test_no_active_repos_shows_zzz() -> None:
    repo = RepositoryProductivityMetrics(repository_name="org/idle-repo", merged_prs_count=0, lines_added=0, lines_deleted=0)
    metrics = _make_metrics(repository_breakdown=[repo])
    text = _extract_text(formatter.get_messages_for_team_metrics(metrics))
    assert ":zzz:" in text


# Reviewer truncation to 5
def test_reviewer_truncation_to_5() -> None:
    approvals = {f"user{i}": 10 - i for i in range(8)}
    metrics = _make_metrics(reviewer_approvals=approvals)
    text = _extract_text(formatter.get_messages_for_team_metrics(metrics))
    # Only first 5 should appear
    assert "user0" in text
    assert "user4" in text
    assert "user5" not in text


# Approval pluralization
def test_approval_singular() -> None:
    metrics = _make_metrics(reviewer_approvals={"alice": 1})
    text = _extract_text(formatter.get_messages_for_team_metrics(metrics))
    assert "1 approval" in text
    assert "1 approvals" not in text


def test_approval_plural() -> None:
    metrics = _make_metrics(reviewer_approvals={"alice": 3})
    text = _extract_text(formatter.get_messages_for_team_metrics(metrics))
    assert "3 approvals" in text


# Medal emojis for top 3
def test_medal_emojis() -> None:
    approvals = {"gold": 10, "silver": 8, "bronze": 5}
    metrics = _make_metrics(reviewer_approvals=approvals)
    text = _extract_text(formatter.get_messages_for_team_metrics(metrics))
    assert ":first_place_medal:" in text
    assert ":second_place_medal:" in text
    assert ":third_place_medal:" in text


# Time window in header
def test_time_window_in_header() -> None:
    metrics = _make_metrics(time_window_days=7)
    text = _extract_text(formatter.get_messages_for_team_metrics(metrics))
    assert "Last 7 days" in text
