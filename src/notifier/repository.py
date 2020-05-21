from dataclasses import dataclass
from typing import List
from datetime import datetime
import math


@dataclass(frozen=True)
class PullRequest:
	created_at: datetime
	name: str
	url: str
	author: str

	def get_age(self) -> (int, int):
		now = datetime.utcnow()
		difference = now - self.created_at
		days = difference.days
		hours = math.floor(difference.seconds / 3600)
		return (days, hours)



@dataclass(frozen=True)
class Repository:
	name: str
	pulls: List[PullRequest]



def __pull_from_json(data) -> PullRequest:
	return PullRequest(datetime.strptime(data['created_at'], "%Y-%m-%d %H:%M:%S"), data['name'], data['url'], data['author'])

def repository_from_json(data) -> Repository:
	return Repository(data['name'], list(map(__pull_from_json, data['pulls'])))
