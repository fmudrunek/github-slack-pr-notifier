import logging
from typing import List

from repository import RepositoryInfo
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from summary_formatter import RepositorySummaryFormatter

# TODO notification_formatter should have a (interface) type

LOG = logging.getLogger(__name__)


class SlackNotifier:
    def __init__(self, oauth_token: str, notification_formatter: RepositorySummaryFormatter):
        self.client = WebClient(token=oauth_token)
        self.notification_formatter = notification_formatter

    def send_message(self, channel_name: str, repositories: List[RepositoryInfo]) -> None:
        try:
            LOG.info("Sending message to channel #%s)", channel_name)
            result = self.client.chat_postMessage(
                channel=channel_name,
                text="\n\n".join([self.notification_formatter.format_repository(repository) for repository in repositories]),
                unfurl_links=False,
                unfurl_media=False,
            )
            LOG.debug("Slack responded with Result: %s", result)

        except SlackApiError as e:
            raise ValueError(f"Failed to send message to channel #{channel_name}: {e}") from e
