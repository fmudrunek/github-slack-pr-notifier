from notifier.repository import PullRequestInfo, RepositoryInfo
from notifier.slack_client import SlackBlock, SlackBlockKitMessage

"""
Formats the summary message for Slack using Slack's Block Kit format (instead of Markdown which is simpler but less capable)
"""
class SummaryMessageFormatter:

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

   
    def get_messages_for_repo(self, repo: RepositoryInfo) -> list[SlackBlockKitMessage]:
        results = []
        for index, pull in enumerate(repo.pulls):
            formatted_pull = []
            # Append the reposity name header to the first pull request to avoid sending the repo header as a separate message (it looks ugly) 
            if index == 0:
                formatted_pull.append(self.__format_repository_name_header(repo))
            formatted_pull.append(self.__format_pull_request(pull))
            results.append(formatted_pull)
            
        return results

    
    def __format_repository_name_header(self, repo: RepositoryInfo) -> SlackBlock:
        return {"type": "header", "text": {"type": "plain_text", "text": f"{repo.name}"}}
    
    def __format_pull_request(self, pull: PullRequestInfo) -> SlackBlock:
        
        def __format_pull(pull: PullRequestInfo) -> SlackBlock:
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
        
        return {
            # add a bullet point to each pull request
            "type": "rich_text",
            "elements": [
                 {"type": "rich_text_list", "style": "bullet", "border": 1, "elements": [__format_pull(pull)]}
             ]
        }