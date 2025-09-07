from typing import Callable

from notifier.productivity_formatter import ProductivityMessageFormatter
from notifier.repository import TeamProductivityMetrics
from notifier.slack_client import SlackClient


class ProductivityNotifier:
    def __init__(self, slack_client: SlackClient, productivity_formatter: ProductivityMessageFormatter):
        self.client = slack_client
        self.productivity_formatter = productivity_formatter

    def send_productivity_report(
        self, 
        channel_name: str, 
        repository_names: list[str], 
        team_members: list[str],
        time_window_days: int,
        get_team_metrics: Callable[[list[str], list[str], int], TeamProductivityMetrics]
    ) -> None:
        team_metrics = get_team_metrics(repository_names, team_members, time_window_days)
        
        # Only send if there's meaningful data
        if team_metrics.total_merged_prs > 0 or team_metrics.reviewer_approvals:
            messages = self.productivity_formatter.get_messages_for_team_metrics(team_metrics)
            for message in messages:
                self.client.send_message_from_blocks(channel_name, message)