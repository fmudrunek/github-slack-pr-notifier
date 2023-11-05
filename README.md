# Pull Requests Notifier
TODO:
* Short description
* Image of the bot in action
* Describe configuration options


## How to use
The app needs 3 things to run:
1. A **Github token** to be able to access the Github API
2. A **Slack token** to be able to post messages to Slack
3. A **configuration file** to tell the app which repositories to watch and where to post the messages

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
PATH_TO_CONFIG=./config.json
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

### How to run
* Using DockerHub
* Locally
    * Using Docker
    * Using DockerCompose
    * Using Python + Poetry

#### Using Docker Hub

#### Locally
##### Using Docker
The following will build&run a container with env. variables from the `.env` file and the config from `./resources/config.json`. Make sure to update the files first.

    docker build -t pr_notifier .
    docker run --rm --env-file ./.env -v ${pwd}/resources/config.json:/app/resources/config.json:ro pr_notifier

##### Using DockerCompose
For added convenience, a Docker Compose file is available to automatically build and run the container for you, using the configuration from the `.env` and `./resources/config.json` files.

    docker compose up

##### Using Python + Poetry
1. Follow the [Development](#development) section to set up your virtual environment and install dependencies.
2. Run the app

        poetry run python .\src\notifier\main.py


### How to change the name, icon and description of the Slack bot
* Go to [Slack API - Apps](https://api.slack.com/apps), click on your app -> Basic Information -> Scroll down to Display Information.
* Change the name, icon and description. This is what will be displayed in the Slack channel when the bot posts a message.


Modifications/usages
How to run from Docker vs locally

## Development
The application is written in Python and uses [Poetry](https://python-poetry.org/docs/) to manage its dependencies.
Make sure you have [Poetry CLI installed](https://python-poetry.org/docs/#installation).

Create your virtual environment:

    python -m venv venv

and activate it:
On Windows, run:

    venv\Scripts\activate

On Unix or MacOS, run:

    source venv/bin/activate

Alternatively you can use Potery's own virtual environment management. See [Poetry documentation - Managing Environments](https://python-poetry.org/docs/managing-environments/).

Then you can install dependencies

    poetry install

### Run tests, linters and type checkers
Everything is hooked to pytest. You can run all tests and checks with:
    poetry run pytest

### Code formatting
The application is formatted using [black](https://black.readthedocs.io/en/stable/) and [isort](https://pycqa.github.io/isort/).  
You can either run black and isort manually or use prepared [Poe](https://github.com/nat-n/poethepoet) task to format the whole project.

	$ poetry run poe format-code

### Maintainance
To update dependencies within the pinned range, run:

    poetry update

To show dependency updates outside the pinned range:

    poetry show --outdated --top-level