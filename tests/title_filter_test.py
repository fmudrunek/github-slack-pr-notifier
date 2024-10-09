from unittest.mock import Mock
import pytest

from notifier.repository import TitleFilter

def test_title_filter_regex() -> None:
    title_regex = r"^PR-\d+:"
    pr_name = "PR-123: Adding new feature"
    pull_request = Mock(title=pr_name)
    
    matches = TitleFilter(title_regex).applies(pull_request)
    assert matches is True
    
def test_invalid_filter_thows_error() -> None:
    title_regex = r"[SomeInvalidRegex"
    pr_name = "PR-123: Adding new feature"
    pull_request = Mock(title=pr_name)
    
    with pytest.raises(ValueError):
        TitleFilter(title_regex).applies(pull_request)