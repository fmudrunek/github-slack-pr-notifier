import argparse
import logging
import time
from pathlib import Path
from typing import cast

from notifier import properties
from notifier.productivity_formatter import ProductivityMessageFormatter
from notifier.productivity_notifier import ProductivityNotifier
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
    notifications_config: dict[str, properties.NotificationConfig], 
    notification_type_filter: str
) -> dict[str, properties.NotificationConfig]:
    """Filter notifications config to only include specified notification type"""
    filtered_config = {}
    for channel, (notification_type, config) in notifications_config.items():
        if notification_type == notification_type_filter:
            filtered_config[channel] = (notification_type, config)
    
    return filtered_config


def main() -> None:
    start_time = time.time()
    args = parse_args()

    config_path = root_dir / "resources" / "config.json"
    notifications_config = properties.read_config(config_path)
    
    # Filter notifications by type
    filtered_config = filter_notifications_by_type(notifications_config, args.type)
    
    if not filtered_config:
        LOG.warning("No notifications found for type '%s'. Check your configuration.", args.type)
        return
    
    LOG.info("Running %s notifications for %d channel(s)", args.type, len(filtered_config))

    fetcher = PullRequestFetcher(properties.get_github_api_url(), properties.get_github_token())
    slack_client = SlackClient(properties.get_slack_oauth_token())

    # Create both types of notifiers
    pr_notifier = SlackBlockNotifier(slack_client, SummaryMessageFormatter())
    productivity_notifier = ProductivityNotifier(slack_client, ProductivityMessageFormatter())

    run_notifications(filtered_config, fetcher, pr_notifier, productivity_notifier)

    end_time = time.time() - start_time
    LOG.info("Script execution time: %d seconds", int(end_time))


def run_notifications(
    notifications_config: dict[str, properties.NotificationConfig],
    fetcher: PullRequestFetcher,
    pr_notifier: SlackBlockNotifier,
    productivity_notifier: ProductivityNotifier,
) -> None:

    something_failed = False
    for channel, (notification_type, config) in notifications_config.items():
        try:
            if notification_type == "pull_requests":
                pr_config = cast(properties.PullRequestConfig, config)
                pr_notifier.send_report_for_repos(
                    channel, 
                    pr_config["repositories"], 
                    lambda repo_name: fetcher.get_repository_info(repo_name, pr_config["filters"])
                )
            elif notification_type == "team_productivity":
                prod_config = cast(properties.ProductivityConfig, config)
                productivity_notifier.send_productivity_report(
                    channel,
                    prod_config["repositories"],
                    prod_config["team_members"],
                    prod_config["time_window_days"],
                    fetcher.get_team_productivity_metrics
                )
            else:
                LOG.error("Unknown notification type: %s", notification_type)
                something_failed = True
                
        except (ValueError, RuntimeError, ConnectionError) as e:
            LOG.error("Failed to send %s notification to channel '%s' with message: %s", notification_type, channel, str(e))
            something_failed = True

    if something_failed:
        raise ValueError("Failed to send some of the messages. See Errors in the logs above for more details.")


if __name__ == "__main__":
    main()
