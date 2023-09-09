import logging
from pathlib import Path
from typing import Dict, List

from notifier.pull_request_fetcher import PullRequestFetcher
import notifier.properties as properties
from notifier.repository import RepositoryInfo
from notifier.slack_notifier import SlackNotifier
from notifier.summary_formatter import RepositorySummaryFormatter

# TODO rewrite to __main__.py

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s (%(filename)s) %(message)s', datefmt='%d-%m-%y %H:%M:%S')

def main():
    config_path = Path(__file__).resolve().parent / 'resources' / 'config.json'
    slack_repositories_config = properties.read_config(config_path)

    fetcher = PullRequestFetcher(properties.get_github_api_url(),
                                 properties.get_github_token())

    channel_repositories = {}
    for (channel, repository_names) in slack_repositories_config.items():
        channel_repositories[channel] = [fetcher.get_repository_info(repo_name) for repo_name in repository_names]
    
    
    filtered = __filter_non_empty(channel_repositories)

    slack_notifier = SlackNotifier("Open Pull Requests",
                                   properties.get_slack_bearer_token(),
                                   RepositorySummaryFormatter())

    for (channel, repositories) in filtered.items():
        slack_notifier.send_message(channel, repositories)


def __filter_non_empty(channel_to_repository: Dict[str, List[RepositoryInfo]]) -> Dict[str, List[RepositoryInfo]]:
    return {
        channel: [repo for repo in repositories if repo.pulls]  # filter repositories with some PRs
        for (channel, repositories) in channel_to_repository.items() if any(repo.pulls for repo in repositories)
        # only add channel if it has at least one repo with PRs
    }


if __name__ == "__main__":
    main()
