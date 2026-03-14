from unittest.mock import Mock

from main import filter_notifications_by_type, run_notifications
from notifier.properties import ProductivityNotification, PullRequestNotification
from notifier.repository import AuthorFilter, DraftFilter


def test_run_notifications_with_pull_requests() -> None:
    notifications = [
        PullRequestNotification(slack_channel="channel1", config={"repositories": ["repo1", "repo2"], "filters": [AuthorFilter(["author1"])]}),
        PullRequestNotification(slack_channel="channel2", config={"repositories": ["repo3"], "filters": [DraftFilter(False)]}),
        PullRequestNotification(slack_channel="channel3", config={"repositories": ["repo4"], "filters": []}),
    ]

    fetcher = Mock()
    pr_notifier = Mock()
    productivity_notifier = Mock()

    run_notifications(notifications, fetcher, pr_notifier, productivity_notifier)

    assert pr_notifier.send_report_for_repos.call_count == 3
    productivity_notifier.send_productivity_report.assert_not_called()


def test_run_notifications_with_productivity() -> None:
    notifications = [
        ProductivityNotification(slack_channel="team-channel", config={"repositories": ["repo1"], "team_members": ["dev1", "dev2"], "time_window_days": 14}),
    ]

    fetcher = Mock()
    pr_notifier = Mock()
    productivity_notifier = Mock()

    run_notifications(notifications, fetcher, pr_notifier, productivity_notifier)

    productivity_notifier.send_productivity_report.assert_called_once_with(
        "team-channel", ["repo1"], ["dev1", "dev2"], 14, fetcher.get_team_productivity_metrics
    )
    pr_notifier.send_report_for_repos.assert_not_called()


def test_filter_notifications_by_type_pull_requests() -> None:
    notifications = [
        PullRequestNotification(slack_channel="pr-channel-1", config={"repositories": ["repo1"], "filters": [AuthorFilter(["user1"])]}),
        ProductivityNotification(slack_channel="productivity-channel", config={"repositories": ["repo2"], "team_members": ["dev1"], "time_window_days": 14}),
        PullRequestNotification(slack_channel="pr-channel-2", config={"repositories": ["repo3"], "filters": []}),
    ]

    filtered = filter_notifications_by_type(notifications, "pull_requests")

    assert len(filtered) == 2
    assert all(isinstance(n, PullRequestNotification) for n in filtered)
    channels = [n.slack_channel for n in filtered]
    assert "pr-channel-1" in channels
    assert "pr-channel-2" in channels


def test_filter_notifications_by_type_team_productivity() -> None:
    notifications = [
        PullRequestNotification(slack_channel="pr-channel-1", config={"repositories": ["repo1"], "filters": [AuthorFilter(["user1"])]}),
        ProductivityNotification(slack_channel="productivity-channel-1", config={"repositories": ["repo2"], "team_members": ["dev1"], "time_window_days": 14}),
        ProductivityNotification(slack_channel="productivity-channel-2", config={"repositories": ["repo3"], "team_members": ["dev2", "dev3"], "time_window_days": 7}),
        PullRequestNotification(slack_channel="pr-channel-2", config={"repositories": ["repo4"], "filters": []}),
    ]

    filtered = filter_notifications_by_type(notifications, "team_productivity")

    assert len(filtered) == 2
    assert all(isinstance(n, ProductivityNotification) for n in filtered)
    channels = [n.slack_channel for n in filtered]
    assert "productivity-channel-1" in channels
    assert "productivity-channel-2" in channels
