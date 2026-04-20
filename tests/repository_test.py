from unittest.mock import Mock

from notifier.repository import AuthorFilter
from notifier.repository import _get_review_status as get_review_status


# ---------- AuthorFilter ----------

def _make_pr(author_login, requested_reviewers=None, reviews=None):
    pr = Mock()
    pr.user.login = author_login
    users = [Mock(login=login) for login in (requested_reviewers or [])]
    pr.get_review_requests.return_value = (users, [])
    review_objs = []
    for login, state in reviews or []:
        r = Mock()
        r.user.login = login
        r.state = state
        review_objs.append(r)
    pr.get_reviews.return_value = review_objs
    return pr


def test_author_filter_empty_authors_allows_all():
    pr = _make_pr("anyone")
    assert AuthorFilter([]).applies(pr) is True


def test_author_filter_matches_direct_author():
    pr = _make_pr("test-author")
    assert AuthorFilter(["test-author"]).applies(pr) is True


def test_author_filter_rejects_non_matching_author():
    pr = _make_pr("someone-else")
    assert AuthorFilter(["test-author"]).applies(pr) is False


def test_author_filter_copilot_with_requested_reviewer_in_authors():
    pr = _make_pr("Copilot", requested_reviewers=["test-author"])
    assert AuthorFilter(["test-author"]).applies(pr) is True


def test_author_filter_copilot_swe_agent_login_detected():
    pr = _make_pr("copilot-swe-agent", requested_reviewers=["test-author"])
    assert AuthorFilter(["test-author"]).applies(pr) is True


def test_author_filter_copilot_falls_back_to_first_non_bot_approver():
    pr = _make_pr(
        "Copilot",
        requested_reviewers=[],
        reviews=[
            ("copilot-pull-request-reviewer", "APPROVED"),
            ("test-author", "APPROVED"),
        ],
    )
    assert AuthorFilter(["test-author"]).applies(pr) is True


def test_author_filter_copilot_ignores_non_approved_reviews_in_fallback():
    pr = _make_pr(
        "Copilot",
        requested_reviewers=[],
        reviews=[("test-author", "COMMENTED")],
    )
    assert AuthorFilter(["test-author"]).applies(pr) is False


def test_author_filter_copilot_with_no_reviewers_rejected():
    pr = _make_pr("Copilot", requested_reviewers=[], reviews=[])
    assert AuthorFilter(["test-author"]).applies(pr) is False


def test_author_filter_copilot_prefers_requested_reviewer_over_approver():
    pr = _make_pr(
        "Copilot",
        requested_reviewers=["someone-else"],
        reviews=[("test-author", "APPROVED")],
    )
    # requested reviewer takes precedence, and they don't match authors list
    assert AuthorFilter(["test-author"]).applies(pr) is False


# ---------- _get_review_status ----------

class DummyReview:
    def __init__(self, user, state):
        self.user = Mock()
        self.user.login = user
        self.state = state

class DummyPaginatedList(list):
    @property
    def totalCount(self):   # pylint: disable=invalid-name
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

def test_empty_required_reviewers_falls_back_to_all_reviewers_waiting():
    reviews = make_reviews(("alice", "APPROVED"), ("bob", "COMMENTED"))
    assert get_review_status(reviews, []) == "WAITING"

def test_empty_required_reviewers_falls_back_to_all_reviewers_approved():
    reviews = make_reviews(("alice", "APPROVED"), ("bob", "APPROVED"))
    assert get_review_status(reviews, []) == "APPROVED"
