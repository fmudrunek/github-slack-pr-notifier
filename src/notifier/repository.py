from dataclasses import dataclass
from datetime import datetime
import math
from github import PullRequest
from typing import List


@dataclass(frozen=True)
class PullRequestInfo:
    name: str
    author: str
    created_at: datetime
    age: (int, int)
    review_status: str
    url: str

    @classmethod
    def from_pull_request(cls, pull_request: PullRequest):
        return cls(name=pull_request.title,
                   author=pull_request.user.login,
                   created_at=pull_request.created_at,
                   age=cls.__get_age(pull_request.created_at),
                   review_status="TBD",
                   url=pull_request.html_url)

    @staticmethod
    def __get_age(from_when: datetime) -> (int, int):
        now = datetime.utcnow()
        difference = now - from_when
        days = difference.days
        hours = math.floor(difference.seconds / 3600)
        return (days, hours)


@dataclass(frozen=True)
class RepositoryInfo:
    name: str
    pulls: List[PullRequestInfo]
