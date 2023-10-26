import json
import os
from pathlib import Path
from typing import Dict, List, TypeAlias

from repository import AuthorFilter, DraftFilter, PullRequestFilter


def __get_env(env_variable: str) -> str:
    if env_variable not in os.environ:
        raise ValueError(f"Environment variable '{env_variable}' not found")
    return os.environ[env_variable]


def get_github_token() -> str:
    return __get_env("GITHUB_TOKEN")


def get_slack_oauth_token() -> str:
    return __get_env("SLACK_OAUTH_TOKEN")


def get_github_api_url() -> str:
    return __get_env("GITHUB_REST_API_URL")


ChannelConfig: TypeAlias = tuple[List[str], List[PullRequestFilter]]  # (repository_names, pull_request_filters)


def read_config(config_path: Path) -> Dict[str, ChannelConfig]:
    with open(config_path) as json_data_file:
        config = json.load(json_data_file)
    return {entry["slack_channel"]: (entry["repositories"], __parse_filters(entry)) for entry in config["notifications"]}


def __parse_filters(config_entry) -> List[PullRequestFilter]:
    if "pull_request_filters" not in config_entry:
        return []

    filters = config_entry["pull_request_filters"]
    result = []
    if "authors" in filters:
        result.append(AuthorFilter(filters["authors"]))
    if "include_drafts" in filters:
        result.append(DraftFilter(filters["include_drafts"]))

    return result
