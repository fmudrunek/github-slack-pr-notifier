import logging
import time
from pathlib import Path
from typing import Callable

from notifier import properties
from notifier.pull_request_fetcher import PullRequestFetcher
from notifier.repository import PullRequestFilter, RepositoryInfo
from notifier.slack_client import SlackClient
from notifier.slack_notifier import SlackBlockNotifier
from notifier.summary_formatter import SummaryMessageFormatter

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s (%(filename)s:%(lineno)d) %(message)s", datefmt="%d-%m-%y %H:%M:%S")

root_dir = Path(__file__).resolve().parents[1]


def main() -> None:
    start_time = time.time()

    config_path = root_dir / "resources" / "config.json"
    slack_repositories_config = properties.read_config(config_path)

    fetcher = PullRequestFetcher(properties.get_github_api_url(), properties.get_github_token())
    slack_client = SlackClient(properties.get_slack_oauth_token())

    slack_notifier = SlackBlockNotifier(slack_client, SummaryMessageFormatter())

    run_notifier(slack_repositories_config, fetcher.get_repository_info, slack_notifier.send_report_for_repos)

    end_time = time.time() - start_time
    LOG.info("Script execution time: %d seconds", int(end_time))


def run_notifier(
    slack_repositories_config: dict[str, properties.ChannelConfig],
    get_repository_info: Callable[[str, list[PullRequestFilter]], RepositoryInfo],
    send_message: Callable[[str, list[str], Callable[[str], RepositoryInfo]], None],
) -> None:

    something_failed = False
    for channel, channel_config in slack_repositories_config.items():
        (repository_names, pr_filters) = channel_config

        try:
            send_message(channel, repository_names, lambda repo_name: get_repository_info(repo_name, pr_filters))
        except Exception as e:
            LOG.error("Failed to send message to channel '%s' with message: %s", channel, str(e))
            something_failed = True

    if something_failed:
        raise ValueError("Failed to send some of the messages. See Errors in the logs above for more details.")


if __name__ == "__main__":
    main()
