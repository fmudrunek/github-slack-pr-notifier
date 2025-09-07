from pathlib import Path
from notifier import properties
from notifier.repository import AuthorFilter, DraftFilter
import pytest

def get_test_config_path() -> Path:
    test_root_dir = Path(__file__).resolve().parent
    return test_root_dir / "test_resources" / "test_config.json"

def create_config_file(tmp_path, config, filename="config.json"):
    import json
    config_path = tmp_path / filename
    if isinstance(config, str):
        with open(config_path, "w") as f:
            f.write(config)
    else:
        with open(config_path, "w") as f:
            json.dump(config, f)
    return config_path

def test_config_parsing() -> None:
    test_config_path = get_test_config_path()
    actual_parsed_config = properties.read_config(test_config_path)

    expected_parsed_config: dict[str, properties.NotificationConfig] = {
        "test-slack-channel1": ("pull_requests", {"repositories": ["testUser1/test-repo1"], "filters": [AuthorFilter(["testUser1"]), DraftFilter(False)]}),
        "test-slack-channel2": ("pull_requests", {"repositories": ["testUser2/test-repo2", "testUser2/test-repo3"], "filters": []}),
    }

    assert actual_parsed_config == expected_parsed_config

def test_trimming_and_deduplication_of_repositories_and_authors(tmp_path):
    from notifier.repository import AuthorFilter, DraftFilter
    config = {
        "notifications": [
            {
                "slack_channel": "test-channel",
                "repositories": [" repo1 ", "repo1", "repo2", "repo2 "],
                "pull_request_filters": {
                    "authors": [" alice ", "bob", "alice", " bob ", "alice"],
                    "include_drafts": True
                }
            }
        ]
    }
    config_path = create_config_file(tmp_path, config)
    parsed = properties.read_config(config_path)
    notification_type, config = parsed["test-channel"]
    assert notification_type == "pull_requests"
    repositories = config["repositories"]
    filters = config["filters"]
    assert repositories == ["repo1", "repo2"]  # repositories trimmed and deduplicated, order preserved
    assert any(isinstance(f, AuthorFilter) and f.authors == ["alice", "bob"] for f in filters)
    assert any(isinstance(f, DraftFilter) and f.include_drafts is True for f in filters)

def test_missing_pull_request_filters(tmp_path):
    config = {
        "notifications": [
            {
                "slack_channel": "chan",
                "repositories": ["repo"],
            }
        ]
    }
    config_path = create_config_file(tmp_path, config)
    parsed = properties.read_config(config_path)
    notification_type, config = parsed["chan"]
    assert notification_type == "pull_requests"
    repositories = config["repositories"]
    filters = config["filters"]
    assert repositories == ["repo"]
    assert filters == []

def test_invalid_json(tmp_path):
    bad_json = "not json"
    config_path = create_config_file(tmp_path, bad_json, filename="bad.json")
    import pytest
    with pytest.raises(ValueError):
        properties.read_config(config_path)

def test_empty_config(tmp_path):
    config = {}
    config_path = create_config_file(tmp_path, config, filename="empty.json")
    import pytest
    with pytest.raises(ValueError):
        properties.read_config(config_path)
