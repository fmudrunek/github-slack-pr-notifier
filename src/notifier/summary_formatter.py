import json
from typing import Any, TypeAlias

from notifier.repository import PullRequestInfo, RepositoryInfo

"""
Formats the summary message for Slack using Slack's Block Kit format (instead of Markdown which is simpler but less capable)
"""


class SummaryMessageFormatter:

    SlackBlock: TypeAlias = dict[str, Any]

    def __get_review_status(self, status: str) -> str:
        return f" {status}" if status in {"APPROVED", "CHANGES_REQUESTED"} else ""

    def __get_code_change_status(self, additions: int, deletions: int, changed_files: int) -> str:
        files = "file" if changed_files == 1 else "files"
        return f"+{additions} -{deletions} in {changed_files} {files}"

    def __get_age_urgency(self, days: int) -> str:
        if days > 9:
            return "alert"
        if days > 4:
            return "warning"

        return ""

    def __format_pull_request(self, pull: PullRequestInfo) -> SlackBlock:
        (days_ago, hours_ago) = pull.age
        if days_ago > 0 and hours_ago >= 12:
            days_ago += 1  # this mimics the behavior of GitHub UI

        age = f"{days_ago} days" if days_ago > 0 else f"{hours_ago} hours"
        age_urgency = self.__get_age_urgency(days_ago)

        review_status = self.__get_review_status(pull.review_status)
        code_change_status = self.__get_code_change_status(pull.additions, pull.deletions, pull.changed_files)

        element_blocks = [
            {"type": "emoji", "name": age_urgency} if age_urgency else None,
            {"type": "link", "url": pull.url, "text": pull.name, "style": {"bold": True}},
            {"type": "text", "text": f"\n{code_change_status}\n{age} ago by {pull.author}"},
            {"type": "text", "text": f"{review_status}", "style": {"bold": True}} if review_status else None,
            {"type": "emoji", "name": "wave"} if review_status else None,
        ]

        return {"type": "rich_text_section", "elements": [block for block in element_blocks if block]}

    def __format_repository(self, repo: RepositoryInfo) -> list[SlackBlock]:
        return [
            {"type": "header", "text": {"type": "plain_text", "text": f"{repo.name}"}},
            {
                "type": "rich_text",
                "elements": [
                    {"type": "rich_text_list", "style": "bullet", "border": 1, "elements": [self.__format_pull_request(pull) for pull in repo.pulls]}
                ],
            },
        ]

    def get_summary_blocks(self, repos: list[RepositoryInfo]) -> str:
        result = []
        repo_blocks = [self.__format_repository(repo) for repo in repos]
        for repo_block in repo_blocks:
            result.extend(repo_block)

        return json.dumps(result)
