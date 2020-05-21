import os
import json


def __get_env(variable):
	if variable not in os.environ:
		raise ValueError(f"Provide '{variable}' environment variable")
	return os.environ[variable]


def get_github_token() -> str:
	return __get_env("github_token")

def get_github_base_url() -> str:
	return "https://git.int.avast.com"

def get_slack_bearer_token() -> str:
	return __get_env("slack_bearer_token")
