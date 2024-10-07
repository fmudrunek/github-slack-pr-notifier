from notifier import properties
from pathlib import Path

from notifier.repository import AuthorFilter, DraftFilter


def get_test_config_path() -> Path:
    test_root_dir = Path(__file__).resolve().parent
    return test_root_dir / "test_resources" / "test_config.json"

def test_config_parsing() -> None:
    test_config_path = get_test_config_path()
    actual_parsed_config = properties.read_config(test_config_path)

    expected_parsed_config: dict[str, properties.ChannelConfig] = {
        "test-slack-channel1": (["testUser1/test-repo1"], [AuthorFilter(["testUser1"]), DraftFilter(False)]),
        "test-slack-channel2": (["testUser2/test-repo2", "testUser2/test-repo3"], []),
    }

    assert actual_parsed_config == expected_parsed_config