from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
import math
from github.PullRequest import PullRequest
from github.PullRequestReview import PullRequestReview
from github.PaginatedList import PaginatedList
from typing import List


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
    return reviews.reversed[0].state if reviews.totalCount > 0 else "WAITING"

def createPullRequestInfo(pull_request: PullRequest) -> PullRequestInfo:
    return PullRequestInfo( name=pull_request.title,
                            author=pull_request.user.login,
                            created_at=pull_request.created_at,
                            age=__get_age(pull_request.created_at),
                            review_status=__get_review_status(pull_request.get_reviews()),
                            url=pull_request.html_url)
