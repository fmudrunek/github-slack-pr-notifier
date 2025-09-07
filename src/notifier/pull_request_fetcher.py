import asyncio
import logging
from datetime import datetime, timedelta, timezone
from itertools import batched
from typing import Any

from github import Auth, Github, UnknownObjectException
from github.GithubException import GithubException
from github.PaginatedList import PaginatedList
from github.PullRequest import PullRequest

from notifier.repository import (
    PullRequestFilter,
    PullRequestInfo,
    RepositoryInfo,
    RepositoryProductivityMetrics,
    TeamProductivityMetrics,
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

    def get_team_productivity_metrics(
        self, repository_names: list[str], team_members: list[str], time_window_days: int
    ) -> TeamProductivityMetrics:
        LOG.info("Fetching team productivity metrics for %d repositories, %d days window", len(repository_names), time_window_days)
        
        since_date = datetime.now(timezone.utc) - timedelta(days=time_window_days)
        repository_metrics = []
        total_merged_prs = 0
        total_lines_added = 0
        total_lines_deleted = 0
        reviewer_approvals: dict[str, int] = {}
        
        for repo_name in repository_names:
            repo_data = self.__get_repository_productivity_data(repo_name, team_members, since_date)
            
            repo_metrics = RepositoryProductivityMetrics(
                repository_name=repo_name,
                merged_prs_count=repo_data["merged_prs_count"],
                lines_added=repo_data["lines_added"],
                lines_deleted=repo_data["lines_deleted"]
            )
            
            repository_metrics.append(repo_metrics)
            total_merged_prs += repo_data["merged_prs_count"]
            total_lines_added += repo_data["lines_added"]
            total_lines_deleted += repo_data["lines_deleted"]
            
            # Aggregate approval counts
            for username, count in repo_data["approvals"].items():
                reviewer_approvals[username] = reviewer_approvals.get(username, 0) + count
        
        LOG.info("Team productivity summary: %d merged PRs, +%d/-%d lines across %d repositories", 
                total_merged_prs, total_lines_added, total_lines_deleted, len(repository_names))
        
        return TeamProductivityMetrics(
            time_window_days=time_window_days,
            total_merged_prs=total_merged_prs,
            total_lines_added=total_lines_added,
            total_lines_deleted=total_lines_deleted,
            repository_breakdown=repository_metrics,
            reviewer_approvals=reviewer_approvals
        )

    def __get_repository_productivity_data(
        self, repository_name: str, team_members: list[str], since_date: datetime
    ) -> dict[str, Any]:
        LOG.info("Fetching productivity data for repository %s", repository_name)
        
        try:
            repo = self.__github.get_repo(repository_name)
        except UnknownObjectException as e:
            raise ValueError(f"Failed to find repository '{repository_name}' in {self.__github_url}", e) from e
        except GithubException as e:
            raise ValueError(f"Failed to retrieve data from {self.__github_url}", e) from e

        # Get closed PRs (which includes merged ones) - fetch once
        closed_pulls = repo.get_pulls(state="closed", sort="updated", direction="desc")
        LOG.info("|-> Found %d closed Pull Requests", closed_pulls.totalCount)
        
        merged_prs_count = 0
        lines_added = 0
        lines_deleted = 0
        approval_counts: dict[str, int] = {}
        
        for pr in closed_pulls:
            LOG.info("|-> Examining PR #%d: '%s'", pr.number, pr.title)
            # Stop if we've gone beyond our time window
            if pr.updated_at and pr.updated_at < since_date:
                break
                
            # Count merged PRs from team members
            if pr.merged and pr.user.login in team_members:
                merged_prs_count += 1
                lines_added += pr.additions
                lines_deleted += pr.deletions
            
            # Count approvals from team members on PRs authored by team members
            if pr.user.login in team_members:
                LOG.info("|-> Checking reviews for PR #%d", pr.number)
                try:
                    reviews = pr.get_reviews()
                    for review in reviews:
                        if (review.state == "APPROVED" and 
                            review.user.login in team_members and
                            review.submitted_at and review.submitted_at >= since_date):
                            reviewer_username = review.user.login
                            LOG.info("|--> Found approval from %s", reviewer_username)
                            approval_counts[reviewer_username] = approval_counts.get(reviewer_username, 0) + 1
                except GithubException:
                    # Skip reviews for this PR if we can't access them
                    continue
        
        LOG.info("|-> Found %d merged PRs with +%d/-%d lines, approvals: %s", 
                merged_prs_count, lines_added, lines_deleted, dict(approval_counts))
        
        return {
            "merged_prs_count": merged_prs_count,
            "lines_added": lines_added,
            "lines_deleted": lines_deleted,
            "approvals": approval_counts
        }
