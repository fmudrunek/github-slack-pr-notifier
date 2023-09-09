import logging
from github import Github, Auth, UnknownObjectException
from github.GithubException import GithubException

from repository import RepositoryInfo, createPullRequestInfo

LOG = logging.getLogger(__name__)
class PullRequestFetcher:

    def __init__(self, github_url: str, token: str):
        self.__github_url = github_url
        auth = Auth.Token(token)
        self.__github = Github(base_url=github_url, auth=auth, retry=3)

    def get_repository_info(self, repository_name: str) -> RepositoryInfo:
        LOG.info(f"Fetching data for repository {repository_name} from {self.__github_url}")
        try:
            repo = self.__github.get_repo(repository_name)
        except UnknownObjectException as e:
            raise ValueError(f"Failed to find repository '{repository_name}' in {self.__github_url}", e)
        except GithubException as e:
            raise ValueError(f"Failed to retrieve data from {self.__github_url}", e)

        pull_requests = repo.get_pulls(state='open', sort='created')
        LOG.info("Found %d open Pull Requests for repository %s", pull_requests.totalCount, repository_name)
        return RepositoryInfo(name=repository_name, pulls=[createPullRequestInfo(pull_request) for pull_request in pull_requests])
