from notifier.repository import RepositoryInfo
from notifier.summary_formatter import SummaryMessageFormatter
from notifier.slack_client import SlackClient


"""
Sending messages to Slack channels using Slack API and the Block Kit formatting.
"""
class SlackBlockNotifier:
    def __init__(self, slack_client: SlackClient, notification_formatter: SummaryMessageFormatter):
        self.client = slack_client
        self.notification_formatter = notification_formatter

    def send_report_for_repos(self, channel_name: str, repositories: list[RepositoryInfo]) -> None:
        for repo in repositories:
            messages = self.notification_formatter.get_messages_for_repo(repo)
            for message in messages:
                self.client.send_message_from_blocks(channel_name, message)
