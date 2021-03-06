import os
import json
from typing import Dict, List


def __get_env(variable):
    if variable not in os.environ:
        raise ValueError(f"Environment variable '{variable}' not found")
    return os.environ[variable]


def get_github_token() -> str:
    return __get_env("GITHUB_TOKEN")


def get_slack_bearer_token() -> str:
    return __get_env("SLACK_BEARER_TOKEN")


def get_github_api_url() -> str:
    return __get_env("GITHUB_REST_API_URL")


def read_config(config_path) -> Dict[str, List[str]]:
    with open(config_path) as json_data_file:
        config = json.load(json_data_file)
    return {entry["slack_channel"]: entry["repositories"] for entry in config['notifications']}
