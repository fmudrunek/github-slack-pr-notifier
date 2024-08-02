import json
import os
from pathlib import Path
from typing import Any, Dict, List, TypeAlias

from dotenv import load_dotenv
from repository import AuthorFilter, DraftFilter, PullRequestFilter

load_dotenv()


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
    try:
        with open(config_path) as json_data_file:
            config = json.load(json_data_file)
    except FileNotFoundError:
        raise FileNotFoundError(f"Config file {config_path} not found.")
    except json.JSONDecodeError:
        raise ValueError(f"Config file {config_path} is not a valid JSON.")
    except IsADirectoryError:
        raise IsADirectoryError(f"Config path {config_path} is a directory. Check that the config path is correct.")
        
    if not config:
            raise ValueError(f"Config file {config_path} is empty")
        
    return {entry["slack_channel"]: (entry["repositories"], __parse_filters(entry)) for entry in config["notifications"]}


def __parse_filters(config_entry: Any) -> List[PullRequestFilter]:
    if "pull_request_filters" not in config_entry:
        return []

    filters = config_entry["pull_request_filters"]
    result = []
    if "authors" in filters:
        result.append(AuthorFilter(filters["authors"]))
    if "include_drafts" in filters:
        result.append(DraftFilter(filters["include_drafts"]))

    return result
