# Pull Requests Notifier
A simple, configurable tool to send GitHub Pull Request summaries to Slack.

Using a simple JSON configuration file, you can configure the app to watch multiple repositories and post summaries to multiple Slack channels.


## How to use
The app needs 3 things to run:
1. A **Github token** to be able to access the Github API
2. A **Slack token** to be able to post messages to Slack
3. A **JSON configuration file** to tell the app which repositories to watch and where to post the messages

### Required integration tokens
1. Get a Github token
    1. See [Github documentation](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens) on how to generate an acces token.
    `TL;DR: Go to Settings -> Developer settings -> Personal access tokens -> Fine-grained tokens -> Generate new token.`
    2. Select your organization as the Resource Owner to be able to access private repositories.
    3. In the Repository Access section, select All repositories (or Selected Repositoreis).
    4. Add Repository permission: `Pull requests: Read-only`.
2. Get a Slack token
    1. Create a Slack app
        1. Go to [Slack API - Apps](https://api.slack.com/apps), click Create New App -> From scratch.
    2. Add necessary permissions
        1. In your app settings, go to "OAuth & Permissions".
        2. In "Bot Token Scopes" add the `chat:write.public` scope.
    3. Click `Install to your workspace`
    4. Copy the OAuth token

### Environment variables
The application will load env variables either from the environment or from a `.env` file when it is present (which can be useful for local run/testing).
See [.env.example](./.env.example)
```
GITHUB_BASE_URL=https://github.com
GITHUB_TOKEN=
SLACK_OAUTH_TOKEN=
```

### Configuration
See [config_example.json](./config_example.json)
```json
{
    "notifications": [
		{
			"slack_channel": "notifier-integration-test",
			"repositories": ["fmudrunek/github-slack-pr-notifier"],
			"pull_request_filters": {
				"authors": ["fmudrunek"],
				"include_drafts": false
			}
		},
		{
			"slack_channel": "notifier-integration-test-2",
			"repositories": ["PyGithub/PyGithub", "adam-p/markdown-here"]
		}
	]
}
```
Each object in the `notifications` array represents a single notification configuration. The app will watch all the repositories listed in the `repositories` array and post summaries to the Slack channel specified in the `slack_channel` field.

The `pull_request_filters` object is optional. If it is present, the app will only post summaries for pull requests that match the filters. If it is not present, the app will post summaries for all pull requests.
Available filters:
* `authors` - a list of Github usernames. If present, the app will only post summaries for pull requests created by the specified users.
* `include_drafts` - a boolean. If `true`, the app will post summaries for draft pull requests. If `false`, the app will ignore draft pull requests.

### How to run
Before you run the app, make sure you have already setup the `.env` file and the `config.json` file.
#### Directly from Docker Hub
The app is available as a Docker image [fmudrunek/github-slack-pr-notifier](https://hub.docker.com/r/fmudrunek/github-slack-pr-notifier) on Docker Hub so it can be run directly. Just mount a `config.json` into /app/resources in the container:

    docker run --rm --env-file ./.env -v ${pwd}/my_config.json:/app/resources/config.json:ro fmudrunek/github-slack-pr-notifier:latest

#### Locally
##### Using Docker
Add your configuration to `/resources/config.json` and run the following commands:

    docker build -t pr_notifier .
    docker run --rm --env-file ./.env -v ${pwd}/resources/config.json:/app/resources/config.json:ro pr_notifier

##### Using DockerCompose
For added convenience, a Docker Compose file is available to automatically build and run the container for you, using the configuration from the `.env` and `./resources/config.json` file.

    docker compose up

##### Using Python + Poetry
1. Follow the [Development](#development) section to set up your virtual environment and install dependencies.
2. Run the app. It will be looking into `./resources/config.json` for the configuration.

        poetry run python .\src\main.py


### How to change the name, icon and description of the Slack bot
* Go to [Slack API - Apps](https://api.slack.com/apps), click on your app -> Basic Information -> Scroll down to Display Information.
* Change the name, icon and description. This is what will be displayed in the Slack channel when the bot posts a message.


## Development
For details on work with the code/project, how to run tests, formatters & how to to do maintenance work see the [Developer README.md](./src/notifier/README.md)