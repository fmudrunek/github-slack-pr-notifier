from unittest.mock import Mock

from main import run_notifications, filter_notifications_by_type
from notifier import properties
from notifier.repository import AuthorFilter, DraftFilter


def test_run_notifications_with_pull_requests() -> None:
    # Define sample notifications config with pull request notifications
    notifications_config: dict[str, properties.NotificationConfig] = {
        "channel1": ("pull_requests", {"repositories": ["repo1", "repo2"], "filters": [AuthorFilter(["author1"])]}),
        "channel2": ("pull_requests", {"repositories": ["repo3"], "filters": [DraftFilter(False)]}),
        "channel3": ("pull_requests", {"repositories": ["repo4"], "filters": []}),
    }
    
    fetcher = Mock()
    pr_notifier = Mock()
    productivity_notifier = Mock()
    
    # Call the run_notifications function
    run_notifications(notifications_config, fetcher, pr_notifier, productivity_notifier)
    
    # Check that pr_notifier was called with the correct arguments
    assert pr_notifier.send_report_for_repos.call_count == 3
    productivity_notifier.send_productivity_report.assert_not_called()


def test_run_notifications_with_productivity() -> None:
    # Define sample notifications config with productivity notifications
    notifications_config: dict[str, properties.NotificationConfig] = {
        "team-channel": ("team_productivity", {"repositories": ["repo1"], "team_members": ["dev1", "dev2"], "time_window_days": 14}),
    }
    
    fetcher = Mock()
    pr_notifier = Mock()
    productivity_notifier = Mock()
    
    # Call the run_notifications function
    run_notifications(notifications_config, fetcher, pr_notifier, productivity_notifier)
    
    # Check that productivity_notifier was called with the correct arguments
    productivity_notifier.send_productivity_report.assert_called_once_with(
        "team-channel", ["repo1"], ["dev1", "dev2"], 14, fetcher.get_team_productivity_metrics
    )
    pr_notifier.send_report_for_repos.assert_not_called()


def test_filter_notifications_by_type_pull_requests() -> None:
    # Define mixed notifications config
    notifications_config: dict[str, properties.NotificationConfig] = {
        "pr-channel-1": ("pull_requests", {"repositories": ["repo1"], "filters": [AuthorFilter(["user1"])]}),
        "productivity-channel": ("team_productivity", {"repositories": ["repo2"], "team_members": ["dev1"], "time_window_days": 14}),
        "pr-channel-2": ("pull_requests", {"repositories": ["repo3"], "filters": []}),
    }
    
    # Filter for pull_requests only
    filtered = filter_notifications_by_type(notifications_config, "pull_requests")
    
    # Should only contain pull_requests notifications
    assert len(filtered) == 2
    assert "pr-channel-1" in filtered
    assert "pr-channel-2" in filtered
    assert "productivity-channel" not in filtered
    
    # Verify the content is correct
    assert filtered["pr-channel-1"][0] == "pull_requests"
    assert filtered["pr-channel-2"][0] == "pull_requests"


def test_filter_notifications_by_type_team_productivity() -> None:
    # Define mixed notifications config
    notifications_config: dict[str, properties.NotificationConfig] = {
        "pr-channel-1": ("pull_requests", {"repositories": ["repo1"], "filters": [AuthorFilter(["user1"])]}),
        "productivity-channel-1": ("team_productivity", {"repositories": ["repo2"], "team_members": ["dev1"], "time_window_days": 14}),
        "productivity-channel-2": ("team_productivity", {"repositories": ["repo3"], "team_members": ["dev2", "dev3"], "time_window_days": 7}),
        "pr-channel-2": ("pull_requests", {"repositories": ["repo4"], "filters": []}),
    }
    
    # Filter for team_productivity only
    filtered = filter_notifications_by_type(notifications_config, "team_productivity")
    
    # Should only contain team_productivity notifications
    assert len(filtered) == 2
    assert "productivity-channel-1" in filtered
    assert "productivity-channel-2" in filtered
    assert "pr-channel-1" not in filtered
    assert "pr-channel-2" not in filtered
    
    # Verify the content is correct
    assert filtered["productivity-channel-1"][0] == "team_productivity"
    assert filtered["productivity-channel-2"][0] == "team_productivity"


def test_filter_notifications_by_type_empty_result() -> None:
    # Define config with only one type
    notifications_config: dict[str, properties.NotificationConfig] = {
        "pr-channel": ("pull_requests", {"repositories": ["repo1"], "filters": []}),
    }
    
    # Filter for the other type
    filtered = filter_notifications_by_type(notifications_config, "team_productivity")
    
    # Should be empty
    assert len(filtered) == 0
    assert filtered == {}


def test_filter_notifications_by_type_preserves_config_structure() -> None:
    # Define notifications config
    original_config = {"repositories": ["repo1", "repo2"], "filters": [AuthorFilter(["user1"]), DraftFilter(False)]}
    notifications_config: dict[str, properties.NotificationConfig] = {
        "test-channel": ("pull_requests", original_config)
    }
    
    # Filter should preserve the exact config structure
    filtered = filter_notifications_by_type(notifications_config, "pull_requests")
    
    assert len(filtered) == 1
    notification_type, config = filtered["test-channel"]
    assert notification_type == "pull_requests"
    assert config == original_config    
