from .repository import RepositoryInfo, PullRequestInfo


class RepositorySummaryFormatter:

    def format_repository(self, repo: RepositoryInfo) -> str:
        return f"*{repo.name}*\n" + "\n".join(map(self.__format_pull_request, repo.pulls))

    def __format_pull_request(self, pull: PullRequestInfo) -> str:
        (days_ago, hours_ago) = pull.age
        age = f"{days_ago} days" if days_ago > 0 else f"{hours_ago} hours"
        age_urgency = self.__get_age_urgency(days_ago)
        return f"- <{pull.url}|{pull.name}> ({age} ago by {pull.author}) {age_urgency}"

    def __get_age_urgency(self, days):
        if days > 9:
            return ":redalert: "
        elif days > 7:
            return ":alert:"
        else:
            return ""
