from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List

from github.PaginatedList import PaginatedList
from github.PullRequest import PullRequest
from github.PullRequestReview import PullRequestReview


@dataclass(frozen=True, slots=True)
class PullRequestInfo:
    name: str
    author: str
    created_at: datetime
    age: tuple[int, int]
    review_status: str
    url: str


@dataclass(frozen=True, slots=True)
class RepositoryInfo:
    name: str
    pulls: List[PullRequestInfo]


def __get_age(from_when: datetime) -> tuple[int, int]:
    now = datetime.utcnow()
    difference = now - from_when
    days = difference.days
    hours = math.floor(difference.seconds / 3600)
    return (days, hours)


def __get_review_status(reviews: PaginatedList[PullRequestReview]) -> str:
    return str(reviews.reversed[0].state) if reviews.totalCount > 0 else "WAITING"


def create_pull_request_info(pull_request: PullRequest) -> PullRequestInfo:
    return PullRequestInfo(
        name=pull_request.title,
        author=pull_request.user.login,
        created_at=pull_request.created_at,
        age=__get_age(pull_request.created_at),
        review_status=__get_review_status(pull_request.get_reviews()),
        url=pull_request.html_url,
    )


class PullRequestFilter(ABC):
    @abstractmethod
    def applies(self, pull_request: PullRequest) -> bool:
        pass


class AuthorFilter(PullRequestFilter):
    def __init__(self, authors: List[str]) -> None:
        self.authors = authors

    def applies(self, pull_request: PullRequest) -> bool:
        return not self.authors or pull_request.user.login in self.authors


class DraftFilter(PullRequestFilter):
    def __init__(self, include_drafts: bool) -> None:
        self.include_drafts = include_drafts

    def applies(self, pull_request: PullRequest) -> bool:
        return self.include_drafts or pull_request.draft is False
