from repository import PullRequestInfo, RepositoryInfo


class RepositorySummaryFormatter:
    def format_repository(self, repo: RepositoryInfo) -> str:
        return f"*{repo.name}*\n" + "\n".join(self.__format_pull_request(pull) for pull in repo.pulls)

    def __format_pull_request(self, pull: PullRequestInfo) -> str:
        (days_ago, hours_ago) = pull.age
        if days_ago > 0 and hours_ago >= 12:
            days_ago += 1  # this mimics the behavior of GitHub UI

        age = f"{days_ago} days" if days_ago > 0 else f"{hours_ago} hours"
        age_urgency = self.__get_age_urgency(days_ago)
        review_status = self.__get_review_status(pull.review_status)
        return f"- <{pull.url}|{pull.name}> ({age} ago by {pull.author}){age_urgency}{review_status}"

    def __get_review_status(self, status: str) -> str:
        return f" ({status})" if status in {"APPROVED", "CHANGES_REQUESTED"} else ""

    def __get_age_urgency(self, days: int) -> str:
        if days > 9:
            return " :redalert: "
        if days > 7:
            return " :alert:"
        
        return ""
