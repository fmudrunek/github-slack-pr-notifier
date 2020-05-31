from github import Github, UnknownObjectException
from github.GithubException import GithubException

from .repository import RepositoryInfo, PullRequestInfo


class PullRequestFetcher:

    def __init__(self, github_url: str, token: str):
        self.__github_url = github_url
        self.__github = Github(base_url=github_url, login_or_token=token, retry=3)

    def get_repository_info(self, repository_name: str) -> RepositoryInfo:
        try:
            repo = self.__github.get_repo(repository_name)
        except UnknownObjectException:
            raise ValueError(f"Failed to find repository '{repository_name}' in {self.__github_url}")
        except GithubException:
            raise ValueError(f"Failed to retrieve data from {self.__github_url}")

        pull_requests = repo.get_pulls(state='open', sort='created')
        return RepositoryInfo(name=repository_name,
                              pulls=list(map(PullRequestInfo.from_pull_request, pull_requests)))
