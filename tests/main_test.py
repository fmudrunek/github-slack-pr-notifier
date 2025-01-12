from unittest.mock import ANY, Mock

from main import run_notifier
from notifier.repository import AuthorFilter, DraftFilter, PullRequestFilter


def test_run_notifier_with_non_empty_repos() -> None:
    # Define a sample slack_repositories_config
    slack_repositories_config: dict[str, tuple[list[str], list[PullRequestFilter]]] = {
        "channel1": (["repo1", "repo2"], [AuthorFilter(["author1"])]),
        "channel2": (["repo3"], [DraftFilter(False)]),
        "channel3": (["repo4"], []),
    }
    
    get_repository_info = Mock()
    send_message = Mock()
    
    # Call the run_notifier function
    run_notifier(slack_repositories_config, get_repository_info, send_message)
    
    # Check that send_message was called with the correct arguments
    send_message.assert_any_call("channel1", ["repo1", "repo2"], ANY)
    send_message.assert_any_call("channel2", ["repo3"], ANY)
    send_message.assert_any_call("channel3", ["repo4"], ANY)    
