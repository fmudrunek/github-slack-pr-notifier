from github import Github
import json
import properties

token = properties.get_github_token()
api_url = properties.get_github_base_url() + "/api/v3"
g = Github(base_url=api_url, login_or_token=token, retry=3)


def pull_to_info(pullrequest):
	return {'name': pullrequest.title,
			'author': pullrequest.user.login,
			'created_at': str(pullrequest.created_at),
			'url': pullrequest.html_url}

def get_pulls(repository):
	repo = g.get_repo(repository)
	pulls = repo.get_pulls(state='open', sort='created')
	return map(pull_to_info, pulls) 

def write_output(output):
	with open('info.json', 'w') as outfile:
		json.dump(list(output), outfile, indent=4, sort_keys=True)
		outfile.write("\n")


with open("config.json") as json_data_file:
    config = json.load(json_data_file)

result = map(lambda entry: {'channel': entry['slack_channel'], 'repositories': list(map(lambda rep: {'name': rep, 'pulls': list(get_pulls(rep))}, entry['repositories']))}, config)
write_output(result)
