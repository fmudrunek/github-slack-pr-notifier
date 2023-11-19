import logging
from typing import List
import asyncio
from concurrent.futures import ThreadPoolExecutor

from github import Auth, Github, UnknownObjectException
from github.GithubException import GithubException
from github.PaginatedList import PaginatedList
from github.PullRequest import PullRequest
from repository import (
    PullRequestFilter,
    PullRequestInfo,
    RepositoryInfo,
    create_pull_request_info,
)
from itertools import batched

LOG = logging.getLogger(__name__)

CONNECTION_POOL_SIZE = 25

class PullRequestFetcher:
    def __init__(self, github_url: str, token: str):
        self.__github_url = github_url
        auth = Auth.Token(token)
        self.__github = Github(base_url=github_url, auth=auth, retry=3, pool_size=CONNECTION_POOL_SIZE)

    def get_repository_info(self, repository_name: str, pull_request_filters: List[PullRequestFilter]) -> RepositoryInfo:
        LOG.info("Fetching data for repository %s from %s", repository_name, self.__github_url)
        try:
            repo = self.__github.get_repo(repository_name)
        except UnknownObjectException as e:
            raise ValueError(f"Failed to find repository '{repository_name}' in {self.__github_url}", e) from e
        except GithubException as e:
            raise ValueError(f"Failed to retrieve data from {self.__github_url}", e) from e

        pull_requests = repo.get_pulls(state="open", sort="created")
        LOG.info("Found %d open Pull Requests for repository %s", pull_requests.totalCount, repository_name)
        
        filtered_pull_requests = self.__filter_pull_requests(pull_requests, pull_request_filters)
        return RepositoryInfo(name=repository_name, pulls=filtered_pull_requests)

    def __filter_pull_requests(
        self, pull_requests: PaginatedList[PullRequest], pull_request_filters: List[PullRequestFilter]
    ) -> List[PullRequestInfo]:
        filtered = [
            pull_request
            for pull_request in pull_requests
            if all(filter.applies(pull_request) for filter in pull_request_filters)
        ]
        LOG.info("Filtered down to %d Pull Requests", len(filtered))
        pr_infos = asyncio.run(self.__to_pull_request_infos(filtered))
        return pr_infos
        
    async def __to_pull_request_infos(self, pull_requests: List[PullRequest]) -> List[PullRequestInfo]:
        result = []
        for batch in batched(pull_requests, CONNECTION_POOL_SIZE):
            result.extend(await asyncio.gather(*[self.__to_pull_request_info(pull_request) for pull_request in batch]))
        return result
    
    async def __to_pull_request_info(self, pull_request: PullRequest) -> PullRequestInfo:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, create_pull_request_info, pull_request)