import logging
from pathlib import Path

from notifier import properties
from notifier.pull_request_fetcher import PullRequestFetcher
from notifier.repository import RepositoryInfo
from notifier.slack_notifier import SlackBlockNotifier
from notifier.summary_formatter import SummaryMessageFormatter

# TODO rewrite to __main__.py or call this main() from it

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s (%(filename)s:%(lineno)d) %(message)s", datefmt="%d-%m-%y %H:%M:%S")
root_dir = Path(__file__).resolve().parents[1]


def main() -> None:
    config_path = root_dir / "resources" / "config.json"
    slack_repositories_config = properties.read_config(config_path)

    fetcher = PullRequestFetcher(properties.get_github_api_url(), properties.get_github_token())

    channel_repositories: dict[str, list[RepositoryInfo]] = {}
    for channel, channel_config in slack_repositories_config.items():
        (repository_names, pr_filters) = channel_config
        channel_repositories[channel] = [fetcher.get_repository_info(repo_name, pr_filters) for repo_name in repository_names]

    filtered_channels = __filter_non_empty(channel_repositories)

    slack_notifier = SlackBlockNotifier(properties.get_slack_oauth_token(), SummaryMessageFormatter())

    for channel, repositories in filtered_channels.items():
        slack_notifier.send_message(channel, repositories)


def __filter_non_empty(channel_to_repository: dict[str, list[RepositoryInfo]]) -> dict[str, list[RepositoryInfo]]:
    return {
        channel: [repo for repo in repositories if repo.pulls]  # filter repositories with some PRs
        for (channel, repositories) in channel_to_repository.items()
        if any(repo.pulls for repo in repositories)  # only add channel if it has at least one repo with PRs
    }


if __name__ == "__main__":
    main()
