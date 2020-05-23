from github import Github
from .repository import RepositoryInfo, PullRequestInfo


class PullRequestFetcher:
    __api_url_suffix = "/api/v3"

    def __init__(self, github_base_url: str, token: str):
        github_url = github_base_url+self.__api_url_suffix
        self.__github = Github(base_url=github_url, login_or_token=token, retry=3)

    def get_repository_info(self, repository_name: str) -> RepositoryInfo:
        repo = self.__github.get_repo(repository_name)
        pull_requests = repo.get_pulls(state='open', sort='created')
        return RepositoryInfo(name=repository_name,
                              pulls=list(map(PullRequestInfo.from_pull_request, pull_requests)))
