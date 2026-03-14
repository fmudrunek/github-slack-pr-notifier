import argparse
import logging
import time
from pathlib import Path

from notifier import properties
from notifier.productivity_formatter import ProductivityMessageFormatter
from notifier.productivity_notifier import ProductivityNotifier
from notifier.properties import Notification, ProductivityNotification, PullRequestNotification
from notifier.pull_request_fetcher import PullRequestFetcher
from notifier.slack_client import SlackClient
from notifier.slack_notifier import SlackBlockNotifier
from notifier.summary_formatter import SummaryMessageFormatter

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s (%(filename)s:%(lineno)d) %(message)s", datefmt="%d-%m-%y %H:%M:%S")

root_dir = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="GitHub Slack Notifier - Send PR notifications and team productivity reports to Slack",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                           # Run pull request notifications (default)
  python main.py --type pull_requests     # Run only pull request notifications
  python main.py --type team_productivity # Run only team productivity notifications
        """
    )

    parser.add_argument(
        "--type",
        choices=["pull_requests", "team_productivity"],
        default="pull_requests",
        help="Type of notifications to run (default: pull_requests)"
    )

    return parser.parse_args()


def filter_notifications_by_type(
    notifications: list[Notification],
    notification_type_filter: str
) -> list[Notification]:
    """Filter notifications to only include specified notification type"""
    type_map = {
        "pull_requests": PullRequestNotification,
        "team_productivity": ProductivityNotification,
    }
    target_type = type_map.get(notification_type_filter)
    if target_type is None:
        return []
    return [n for n in notifications if isinstance(n, target_type)]


def main() -> None:
    start_time = time.time()
    args = parse_args()

    config_path = root_dir / "resources" / "config.json"
    notifications = properties.read_config(config_path)

    # Filter notifications by type
    filtered = filter_notifications_by_type(notifications, args.type)

    if not filtered:
        LOG.warning("No notifications found for type '%s'. Check your configuration.", args.type)
        return

    LOG.info("Running %s notifications for %d channel(s)", args.type, len(filtered))

    fetcher = PullRequestFetcher(properties.get_github_api_url(), properties.get_github_token())
    slack_client = SlackClient(properties.get_slack_oauth_token())

    # Create both types of notifiers
    pr_notifier = SlackBlockNotifier(slack_client, SummaryMessageFormatter())
    productivity_notifier = ProductivityNotifier(slack_client, ProductivityMessageFormatter())

    run_notifications(filtered, fetcher, pr_notifier, productivity_notifier)

    end_time = time.time() - start_time
    LOG.info("Script execution time: %d seconds", int(end_time))


def run_notifications(
    notifications: list[Notification],
    fetcher: PullRequestFetcher,
    pr_notifier: SlackBlockNotifier,
    productivity_notifier: ProductivityNotifier,
) -> None:

    something_failed = False
    for notification in notifications:
        try:
            if isinstance(notification, PullRequestNotification):
                pr_notifier.send_report_for_repos(
                    notification.slack_channel,
                    notification.config["repositories"],
                    lambda repo_name: fetcher.get_repository_info(repo_name, notification.config["filters"])
                )
            elif isinstance(notification, ProductivityNotification):
                productivity_notifier.send_productivity_report(
                    notification.slack_channel,
                    notification.config["repositories"],
                    notification.config["team_members"],
                    notification.config["time_window_days"],
                    fetcher.get_team_productivity_metrics
                )

        except (ValueError, RuntimeError, ConnectionError) as e:
            LOG.error("Failed to send notification to channel '%s' with message: %s", notification.slack_channel, str(e))
            something_failed = True

    if something_failed:
        raise ValueError("Failed to send some of the messages. See Errors in the logs above for more details.")


if __name__ == "__main__":
    main()
