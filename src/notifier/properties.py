import json
import os
from pathlib import Path
from typing import Any, TypeAlias, TypedDict, Union

from dotenv import load_dotenv

from notifier.repository import (
    AuthorFilter,
    DraftFilter,
    PullRequestFilter,
    TitleFilter,
)

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


class PullRequestConfig(TypedDict):
    repositories: list[str]
    filters: list[PullRequestFilter]

class ProductivityConfig(TypedDict):
    repositories: list[str]
    team_members: list[str]
    time_window_days: int

ChannelConfig = Union[PullRequestConfig, ProductivityConfig]
NotificationConfig: TypeAlias = tuple[str, ChannelConfig]  # (notification_type, config)


def read_config(config_path: Path) -> dict[str, NotificationConfig]:
    try:
        with open(config_path) as json_data_file:
            config = json.load(json_data_file)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Config file {config_path} not found.") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Config file {config_path} is not a valid JSON.") from exc
    except IsADirectoryError as exc:
        raise IsADirectoryError(f"Config path {config_path} is a directory. Check that the config path is correct.") from exc

    if not config:
        raise ValueError(f"Config file {config_path} is empty")

    result: dict[str, NotificationConfig] = {}
    for entry in config["notifications"]:
        channel_name = entry["slack_channel"]
        notification_type = entry.get("type", "pull_requests")  # Default to pull_requests for backward compatibility
        
        if notification_type == "pull_requests":
            pr_config: PullRequestConfig = {
                "repositories": __parse_repositories(entry),
                "filters": __parse_filters(entry)
            }
            result[channel_name] = (notification_type, pr_config)
        elif notification_type == "team_productivity":
            repositories = __parse_repositories(entry)
            team_members = __parse_team_members(entry)
            time_window_days = entry.get("time_window_days", 14)
            if not isinstance(time_window_days, int) or time_window_days <= 0:
                raise ValueError("time_window_days must be a positive integer")
            productivity_config: ProductivityConfig = {
                "repositories": repositories,
                "team_members": team_members,
                "time_window_days": time_window_days
            }
            result[channel_name] = (notification_type, productivity_config)
        else:
            raise ValueError(f"Unknown notification type: {notification_type}")
    
    return result


def __parse_team_members(config_entry: dict[str, Any]) -> list[str]:
    if "team_members" not in config_entry:
        raise ValueError("team_productivity notifications require 'team_members' field")
    
    team_members = []
    for member in config_entry["team_members"]:
        trimmed = member.strip()
        if trimmed and trimmed not in team_members:
            team_members.append(trimmed)
    
    if not team_members:
        raise ValueError("team_productivity notifications require at least one team member")
    
    return team_members


def __parse_repositories(config_entry: dict[str, Any]) -> list[str]:
    result = []
    for repo in config_entry["repositories"]:
        trimmed = repo.strip()
        if trimmed not in result:
            result.append(trimmed)
    return result


def __parse_filters(config_entry: Any) -> list[PullRequestFilter]:
    if "pull_request_filters" not in config_entry:
        return []

    filters = config_entry["pull_request_filters"]
    result: list[PullRequestFilter] = []
    if "authors" in filters:
        trimmed_authors = []
        for a in filters["authors"]:
            trimmed = a.strip()
            if trimmed not in trimmed_authors:
                trimmed_authors.append(trimmed)
        result.append(AuthorFilter(trimmed_authors))
    if "include_drafts" in filters:
        result.append(DraftFilter(filters["include_drafts"]))
    if "title_regex" in filters:
        result.append(TitleFilter(filters["title_regex"]))

    return result
