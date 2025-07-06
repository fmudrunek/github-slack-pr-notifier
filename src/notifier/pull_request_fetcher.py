import asyncio
import logging
from itertools import batched

from github import Auth, Github, UnknownObjectException
from github.GithubException import GithubException
from github.PaginatedList import PaginatedList
from github.PullRequest import PullRequest

from notifier.repository import (
    PullRequestFilter,
    PullRequestInfo,
    RepositoryInfo,
    create_pull_request_info,
)

LOG = logging.getLogger(__name__)

CONNECTION_POOL_SIZE = 25


class PullRequestFetcher:
    def __init__(self, github_url: str, token: str):
        self.__github_url = github_url
        self.__github = Github(base_url=github_url, auth=Auth.Token(token), retry=3, pool_size=CONNECTION_POOL_SIZE)
        self.__cached_pull_requests_for_repos: dict[str, PaginatedList[PullRequest]] = {}

    def get_repository_info(self, repository_name: str, pull_request_filters: list[PullRequestFilter]) -> RepositoryInfo:
        LOG.info("Fetching data for repository %s", repository_name)

        # Check if we have cached data for this repository
        if (cached_pull_requests := self.__cached_pull_requests_for_repos.get(repository_name)) is not None:
            LOG.info("|-> Using cached data for this repo")
            pull_requests = cached_pull_requests
        else:
            try:
                repo = self.__github.get_repo(repository_name)
            except UnknownObjectException as e:
                raise ValueError(f"Failed to find repository '{repository_name}' in {self.__github_url}", e) from e
            except GithubException as e:
                raise ValueError(f"Failed to retrieve data from {self.__github_url}", e) from e

            pull_requests = repo.get_pulls(state="open", sort="created")
            self.__cached_pull_requests_for_repos[repository_name] = pull_requests

        LOG.info("|-> Found %d open Pull Requests", pull_requests.totalCount)

        filtered_pull_requests = self.__filter_pull_requests(pull_requests, pull_request_filters)
        return RepositoryInfo(name=repository_name, pulls=filtered_pull_requests)

    def __filter_pull_requests(
        self, pull_requests: PaginatedList[PullRequest], pull_request_filters: list[PullRequestFilter]
    ) -> list[PullRequestInfo]:
        if pull_requests.totalCount == 0:
            return []

        filtered = []
        for pull_request in pull_requests:
            for filter in pull_request_filters:
                if not filter.applies(pull_request):
                    break
            else:
                filtered.append(pull_request)
        LOG.info("|-> Filtered down to %d Pull Requests", len(filtered))
        pr_infos = asyncio.run(self.__to_pull_request_infos(filtered))
        return pr_infos

    async def __to_pull_request_infos(self, pull_requests: list[PullRequest]) -> list[PullRequestInfo]:
        result = []
        for batch in batched(pull_requests, CONNECTION_POOL_SIZE):
            result.extend(await asyncio.gather(*[self.__to_pull_request_info(pull_request) for pull_request in batch]))
        return result

    async def __to_pull_request_info(self, pull_request: PullRequest) -> PullRequestInfo:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, create_pull_request_info, pull_request)
