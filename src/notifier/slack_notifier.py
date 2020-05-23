import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json
from typing import List

from .repository import RepositoryInfo


# TODO notification_formatter should have a (interface) type

class SlackNotifier:
    def __init__(self, notifier_name: str, slack_bearer_token: str, notification_formatter):
        self.session = get_session(slack_bearer_token)
        self.notifier_name = notifier_name
        self.notification_formatter = notification_formatter

    def send_message(self, slack_channel: str, repositories: List[RepositoryInfo]):
        print(f"Sending message to channel #{slack_channel}")
        slack_notification_params = {
            'channel': slack_channel,
            'text': "\n".join(map(self.notification_formatter.format_repository, repositories)),
            'username': self.notifier_name,
            'unfurl_links': "false"
        }

        try:
            response = self.session.post(url="https://slack.com/api/chat.postMessage",
                                                            data=json.dumps(slack_notification_params))
            response.raise_for_status()
            response_json = response.json()
            if not response_json['ok']:
                raise ValueError(response_json['error'])
        except Exception as e:
            raise ValueError(f"Failed to send message to channel '{slack_channel}'", e)
        else:
            print(response)


def get_session(bearer_token) -> requests.Session:
    headers = {
        'content-type': 'application/json',
        'Authorization': f'Bearer {bearer_token}'
    }
    session = requests.Session()
    session.headers.update(headers)
    return __requests_retry_session(session=session)


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




