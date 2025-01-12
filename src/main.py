import logging
from pathlib import Path
from typing import Callable

from notifier import properties
from notifier.pull_request_fetcher import PullRequestFetcher
from notifier.repository import PullRequestFilter, RepositoryInfo
from notifier.slack_notifier import SlackBlockNotifier
from notifier.summary_formatter import SummaryMessageFormatter
from notifier.slack_client import SlackClient

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s (%(filename)s:%(lineno)d) %(message)s", datefmt="%d-%m-%y %H:%M:%S")
root_dir = Path(__file__).resolve().parents[1]


def main() -> None:
    config_path = root_dir / "resources" / "config.json"
    slack_repositories_config = properties.read_config(config_path)

    fetcher = PullRequestFetcher(properties.get_github_api_url(), properties.get_github_token())
    slack_client = SlackClient(properties.get_slack_oauth_token())
    slack_notifier = SlackBlockNotifier(slack_client, SummaryMessageFormatter())

    run_notifier(slack_repositories_config, fetcher.get_repository_info, slack_notifier.send_report_for_repos)


def run_notifier(
    slack_repositories_config: dict[str, properties.ChannelConfig],
    get_repository_info: Callable[[str, list[PullRequestFilter]], RepositoryInfo],
    send_message: Callable[[str, list[RepositoryInfo]], None],
) -> None:

    channel_repositories: dict[str, list[RepositoryInfo]] = {}
    for channel, channel_config in slack_repositories_config.items():
        (repository_names, pr_filters) = channel_config
        channel_repositories[channel] = [get_repository_info(repo_name, pr_filters) for repo_name in repository_names]

    filtered_channels = __filter_non_empty(channel_repositories)

    for channel, repositories in filtered_channels.items():
        send_message(channel, repositories)


def __filter_non_empty(channel_to_repository: dict[str, list[RepositoryInfo]]) -> dict[str, list[RepositoryInfo]]:
    return {
        channel: [repo for repo in repositories if repo.pulls]  # filter repositories with some PRs
        for (channel, repositories) in channel_to_repository.items()
        if any(repo.pulls for repo in repositories)  # only add channel if it has at least one repo with PRs
    }


if __name__ == "__main__":
    main()
