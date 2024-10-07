from datetime import datetime
from typing import Any
from unittest.mock import Mock

from main import __filter_non_empty, run_notifier
from notifier.repository import (
    AuthorFilter,
    DraftFilter,
    PullRequestFilter,
    PullRequestInfo,
    RepositoryInfo,
)


def test_filter_empty_messages() -> None:
    
    repository_info_3 = RepositoryInfo("repo1", [
        PullRequestInfo("pr_name1", "author1", datetime(2024, 1, 1), (1, 1), "APPROVED", "url1", 1, 1, 1),
    ])
    repository_info_5 = RepositoryInfo("repo2", [
        PullRequestInfo("pr_name2", "author2", datetime(2024, 1, 1), (1, 1), "APPROVED", "url2", 1, 1, 1),
    ])
    repository_info_6 = RepositoryInfo("repo3", [
        PullRequestInfo("pr_name3", "author3", datetime(2024, 1, 1), (1, 1), "APPROVED", "url3", 1, 1, 1),
    ])


    channel_to_repository = {
        "channel1": [RepositoryInfo("empty_repo1", []), RepositoryInfo("empty_repo2", [])],
        "channel2": [repository_info_3, RepositoryInfo("empty_repo4", [])],
        "channel3": [repository_info_5, repository_info_6],
    }

    result = __filter_non_empty(channel_to_repository)
    assert result == {"channel2": [repository_info_3], "channel3": [repository_info_5, repository_info_6]}
    


def test_run_notifier_with_non_empty_repos() -> None:
    # Define a sample slack_repositories_config
    slack_repositories_config: dict[str, tuple[list[str], list[PullRequestFilter]]] = {
        "channel1": (["repo1", "repo2"], [AuthorFilter(["author1"])]),
        "channel2": (["repo3"], [DraftFilter(False)]),
        "channel3": (["repo4"], []),
    }
    
    def mock_get_repository_info(repo_name: str, _: Any) -> RepositoryInfo:
        match repo_name:
            case "repo1":
                return RepositoryInfo("repo1", [PullRequestInfo("PR1", "author1", datetime(2024, 1, 1), (1, 1), "APPROVED", "url1", 1, 1, 1)])
            case "repo2":
                return RepositoryInfo("repo2", [PullRequestInfo("PR1", "author1", datetime(2024, 1, 1), (1, 1), "APPROVED", "url2", 1, 1, 1)])
            case "repo3":
                return RepositoryInfo("repo3", [PullRequestInfo("PR1", "author2", datetime(2024, 1, 1), (1, 1), "APPROVED", "url2", 1, 1, 1)])
            case _:
                return RepositoryInfo("repo4", [])
    
    # Mock the get_repository_info function
    get_repository_info = Mock(side_effect=mock_get_repository_info)

    # Mock the send_message function
    send_message = Mock()

    # Call the run_notifier function
    run_notifier(slack_repositories_config, get_repository_info, send_message)

    # Check that get_repository_info was called with the correct arguments
    get_repository_info.assert_any_call("repo1", [AuthorFilter(["author1"])])
    get_repository_info.assert_any_call("repo2", [AuthorFilter(["author1"])])
    get_repository_info.assert_any_call("repo3", [DraftFilter(False)])
    get_repository_info.assert_any_call("repo4", [])

    # Check that send_message was called with the correct arguments
    send_message.assert_any_call("channel1", [
        RepositoryInfo("repo1", [PullRequestInfo("PR1", "author1", datetime(2024, 1, 1), (1, 1), "APPROVED", "url1", 1, 1, 1)]),
        RepositoryInfo("repo2", [PullRequestInfo("PR1", "author1", datetime(2024, 1, 1), (1, 1), "APPROVED", "url2", 1, 1, 1)])
    ])
    send_message.assert_any_call("channel2", [
        RepositoryInfo("repo3", [PullRequestInfo("PR1", "author2", datetime(2024, 1, 1), (1, 1), "APPROVED", "url2", 1, 1, 1)])
    ])

    
