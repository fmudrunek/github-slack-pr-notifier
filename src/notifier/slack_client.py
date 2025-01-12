import logging
from typing import Any, TypeAlias

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

LOG = logging.getLogger(__name__)

SlackBlock: TypeAlias = dict[str, Any]
SlackBlockKitMessage: TypeAlias = list[SlackBlock]


class SlackClient:
    def __init__(self, oauth_token: str):
        self.client = WebClient(token=oauth_token)

    def send_message_from_blocks(self, channel_name: str, message: SlackBlockKitMessage) -> None:
        try:
            response = self.client.chat_postMessage(
                channel=channel_name,
                blocks=message,
                text="Failed to render content",  # this is a fallback message in case the blocks are not rendered
                unfurl_links=False,
                unfurl_media=False,
            )
            LOG.debug("Slack responded with Result: %s", response)

        except SlackApiError as e:
            raise ValueError(f"Failed to send message to Slack: {e}") from e
