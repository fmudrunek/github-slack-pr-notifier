import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json
from typing import List, Dict

from .repository import Repository, PullRequest, repository_from_json
from . import properties


def get_input():
    with open("info.json") as json_data_file:
        return json.load(json_data_file)


def get_age_urgency(days):
    if days > 9:
        return ":redalert: "
    elif days > 7:
        return ":alert:"
    else:
        return ""


def format_pull_request(pull: PullRequest) -> str:
    (days_ago, hours_ago) = pull.get_age()
    age = f"{days_ago} days" if days_ago > 0 else f"{hours_ago} hours"
    age_urgency = get_age_urgency(days_ago)
    return f"- <{pull.url}|{pull.name}> ({age} ago by {pull.author}) {age_urgency}"


def format_repository(repo: Repository) -> str:
    return f"*{repo.name}*\n" + "\n".join(map(format_pull_request, repo.pulls))


def __requests_retry_session(
        retries=3,
        backoff_factor=0.9,
        status_forcelist=(500, 502, 503, 504),
        session: requests.Session = None,
):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def get_session(bearer_token) -> requests.Session:
    headers = {
        'content-type': 'application/json',
        'Authorization': f'Bearer {bearer_token}'
    }
    session = requests.Session()
    session.headers.update(headers)
    return __requests_retry_session(session=session)


def send_message(slack_channel: str, repositories: List[Repository], session):
    print(f"Sending message to channel #{slack_channel}")
    slack_notification_params = {
        'channel': slack_channel,
        'text': "\n".join(map(format_repository, repositories)),
        'username': 'Open Pull Requests',
        'unfurl_links': "false"
    }

    try:
        slack_notification_response = session.post(url="https://slack.com/api/chat.postMessage",
                                                   data=json.dumps(slack_notification_params))
        slack_notification_response.raise_for_status()
    except Exception as e:
        print(
            f"Failed to send to channel {slack_channel} with error: {e.__class__.__name__}: {e.response} : {e.message}")
    else:
        print(slack_notification_response)


def filter_non_empty(channel_to_repository: Dict[str, List[Repository]]) -> Dict[str, List[Repository]]:
    return {
        channel: [repo for repo in repositories if repo.pulls]  # filter repositories with some PRs
        for (channel, repositories) in channel_to_repository.items() if any(repo.pulls for repo in repositories)
        # only add channel if it has at least one repo with PRs
    }


def run():
    data = get_input()
    channel_repository_dict = {entry['channel']: list(map(repository_from_json, entry['repositories'])) for entry in
                               data}
    filtered = filter_non_empty(channel_repository_dict)
    session = get_session(properties.get_slack_bearer_token())

    for (channel, repositories) in filtered.items():
        send_message(channel, repositories, session)
