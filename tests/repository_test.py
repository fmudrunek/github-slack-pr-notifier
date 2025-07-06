import pytest
from unittest.mock import Mock

from notifier.repository import _PullRequestInfo__get_review_status as get_review_status

class DummyReview:
    def __init__(self, user, state):
        self.user = Mock()
        self.user.login = user
        self.state = state

class DummyPaginatedList(list):
    @property
    def totalCount(self):
        return len(self)

# Helper to create a paginated list of reviews
def make_reviews(*review_tuples):
    return DummyPaginatedList(DummyReview(user, state) for user, state in review_tuples)

def test_no_reviews_returns_waiting():
    reviews = make_reviews()
    assert get_review_status(reviews) == "WAITING"

def test_all_approved_returns_approved():
    reviews = make_reviews(("alice", "APPROVED"), ("bob", "APPROVED"))
    assert get_review_status(reviews) == "APPROVED"

def test_changes_requested_overrides_approved():
    reviews = make_reviews(("alice", "APPROVED"), ("bob", "CHANGES_REQUESTED"))
    assert get_review_status(reviews) == "CHANGES_REQUESTED"

def test_latest_review_per_reviewer_is_used():
    reviews = make_reviews(
        ("alice", "COMMENTED"),
        ("alice", "APPROVED"),  # Only this one counts for alice
        ("bob", "APPROVED"),
    )
    assert get_review_status(reviews) == "APPROVED"

def test_waiting_if_some_not_approved():
    reviews = make_reviews(("alice", "APPROVED"), ("bob", "COMMENTED"))
    assert get_review_status(reviews) == "WAITING"

def test_required_reviewers_approve_and_comment():
    # alice is required and approves, bob is required and only comments
    reviews = make_reviews(
        ("alice", "APPROVED"),
        ("bob", "COMMENTED")
    )
    required_reviewers = ["alice", "bob"]
    assert get_review_status(reviews, required_reviewers) == "WAITING"

def test_required_reviewers_all_approve():
    reviews = make_reviews(
        ("alice", "APPROVED"),
        ("bob", "APPROVED"),
        ("carol", "COMMENTED")  # carol is not required
    )
    required_reviewers = ["alice", "bob"]
    assert get_review_status(reviews, required_reviewers) == "APPROVED"

def test_required_reviewer_changes_requested():
    reviews = make_reviews(
        ("alice", "APPROVED"),
        ("bob", "CHANGES_REQUESTED")
    )
    required_reviewers = ["alice", "bob"]
    assert get_review_status(reviews, required_reviewers) == "CHANGES_REQUESTED"

def test_required_reviewer_missing_review():
    reviews = make_reviews(("alice", "APPROVED"))
    required_reviewers = ["alice", "bob"]
    assert get_review_status(reviews, required_reviewers) == "WAITING"
