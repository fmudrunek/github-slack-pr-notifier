from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone

import regex
from github.PaginatedList import PaginatedList
from github.PullRequest import PullRequest
from github.PullRequestReview import PullRequestReview

COPILOT_AUTHOR_LOGINS = frozenset({"copilot", "copilot-swe-agent"})
# Bot reviewer logins to ignore when picking the "first approver" fallback for Copilot-authored PRs.
_IGNORED_REVIEWER_LOGINS = frozenset({"copilot-pull-request-reviewer", "copilot", "copilot-swe-agent"})


def _is_copilot_author(login: str) -> bool:
    return login.lower() in COPILOT_AUTHOR_LOGINS


def _resolve_copilot_requester(pull_request: PullRequest, requested_reviewer_logins: list[str] | None = None) -> str | None:
    """
    For a Copilot-authored PR, return the human who requested the work.
    Preference: first requested reviewer; fallback: first non-bot approver.
    Pass `requested_reviewer_logins` to avoid a duplicate `get_review_requests` call when the caller already has them.
    """
    if requested_reviewer_logins is None:
        try:
            requested_reviewer_logins = [user.login for user in pull_request.get_review_requests()[0]]
        except (IndexError, AttributeError):
            requested_reviewer_logins = []
    if requested_reviewer_logins:
        return requested_reviewer_logins[0]
    try:
        for review in pull_request.get_reviews():
            if review.state != "APPROVED":
                continue
            login = review.user.login
            if login.lower() in _IGNORED_REVIEWER_LOGINS:
                continue
            if login.lower().endswith("[bot]"):
                continue
            return login
    except (AttributeError, TypeError):
        pass
    return None


@dataclass(frozen=True, slots=True)
class PullRequestInfo:
    name: str
    author: str
    created_at: datetime
    age: tuple[int, int]  # (days, hours)
    review_status: str
    url: str
    additions: int
    deletions: int
    changed_files: int
    copilot_requester: str | None = None


@dataclass(frozen=True, slots=True)
class RepositoryInfo:
    name: str
    pulls: list[PullRequestInfo]


@dataclass(frozen=True, slots=True)
class RepositoryProductivityMetrics:
    repository_name: str
    merged_prs_count: int
    lines_added: int
    lines_deleted: int


@dataclass(frozen=True, slots=True)
class TeamProductivityMetrics:
    time_window_days: int
    total_merged_prs: int
    total_lines_added: int
    total_lines_deleted: int
    repository_breakdown: list[RepositoryProductivityMetrics]
    reviewer_approvals: dict[str, int]  # username -> approval count


def _get_age(from_when: datetime) -> tuple[int, int]:
    now = datetime.now(timezone.utc)
    difference = now - from_when
    days = difference.days
    hours = math.floor(difference.seconds / 3600)
    return (days, hours)


def _get_review_status(reviews: PaginatedList[PullRequestReview], required_reviewers: list[str] | None = None) -> str:
    if reviews.totalCount == 0:
        return "WAITING"
    latest_reviews = {}
    for review in reviews:
        reviewer = review.user.login
        latest_reviews[reviewer] = review
    if not latest_reviews:
        return "WAITING"
    # If required reviewers are specified, only consider their reviews
    if required_reviewers is not None:
        # Check for missing reviews
        for req in required_reviewers:
            if req not in latest_reviews:
                return "WAITING"
        # Check for changes requested
        if any(latest_reviews[req].state == "CHANGES_REQUESTED" for req in required_reviewers):
            return "CHANGES_REQUESTED"
        # All must be approved
        if all(latest_reviews[req].state == "APPROVED" for req in required_reviewers):
            return "APPROVED"
        return "WAITING"
    # Fallback: consider all reviewers
    if any(r.state == "CHANGES_REQUESTED" for r in latest_reviews.values()):
        return "CHANGES_REQUESTED"
    if all(r.state == "APPROVED" for r in latest_reviews.values()):
        return "APPROVED"
    return "WAITING"


def create_pull_request_info(pull_request: PullRequest) -> PullRequestInfo:
    """
    Creates a PullRequestInfo from a PullRequest
    Note that this method does network I/O - it calls the GitHub API to fetch the reviews for given Pull Request.
    """
    # Fetch required reviewers (users only)
    required_reviewers = []
    try:
        reqs = pull_request.get_review_requests()[0]  # returns (users, teams)
        required_reviewers = [user.login for user in reqs]
    except (IndexError, AttributeError):
        pass
    copilot_requester = _resolve_copilot_requester(pull_request, required_reviewers) if _is_copilot_author(pull_request.user.login) else None
    return PullRequestInfo(
        name=pull_request.title,
        author=pull_request.user.login,
        created_at=pull_request.created_at,
        age=_get_age(pull_request.created_at),
        review_status=_get_review_status(pull_request.get_reviews(), required_reviewers),
        url=pull_request.html_url,
        additions=pull_request.additions,
        deletions=pull_request.deletions,
        changed_files=pull_request.changed_files,
        copilot_requester=copilot_requester,
    )


class PullRequestFilter(ABC):
    @abstractmethod
    def applies(self, pull_request: PullRequest) -> bool:
        pass


@dataclass(frozen=True, slots=True)
class AuthorFilter(PullRequestFilter):
    authors: list[str]

    def applies(self, pull_request: PullRequest) -> bool:
        if not self.authors:
            return True
        if pull_request.user.login in self.authors:
            return True
        if _is_copilot_author(pull_request.user.login):
            requester = _resolve_copilot_requester(pull_request)
            return requester is not None and requester in self.authors
        return False


@dataclass(frozen=True, slots=True)
class DraftFilter(PullRequestFilter):
    include_drafts: bool

    def applies(self, pull_request: PullRequest) -> bool:
        return self.include_drafts or pull_request.draft is False


@dataclass()
class TitleFilter(PullRequestFilter):
    title_regex: str
    compiled_pattern: regex.Pattern = field(init=False)

    def __post_init__(self) -> None:
        try:
            self.compiled_pattern = regex.compile(self.title_regex)
        except regex.error as e:
            raise ValueError(f"The provided regex is invalid: {e}") from e

    def applies(self, pull_request: PullRequest) -> bool:
        try:
            match = self.compiled_pattern.search(pull_request.title, timeout=0.1)  # 100ms timeout
            return match is not None
        except TimeoutError as e:
            raise ValueError("The provided regex is too complex and timed out.") from e
