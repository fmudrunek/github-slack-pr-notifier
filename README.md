# GitHub Slack Notifier
A configurable tool to send GitHub notifications to Slack channels.

Using a JSON configuration file, you can configure the app to:
- Send Pull Request summaries to Slack channels
- Send team productivity reports with merged PR metrics and review statistics


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
The app supports two types of notifications: Pull Request notifications and Team Productivity notifications.
For a full config example see [config_example.json](./resources/config_example.json).

#### Pull Request Notifications
```json
{
    "notifications": [
        {
            "type": "pull_requests",
            "slack_channel": "pr-notifications",
            "repositories": ["org/repo1", "org/repo2"],
            "pull_request_filters": {
                "authors": ["dev1", "dev2"],
                "include_drafts": false,
                "title_regex": "^feat:"
            }
        }
    ]
}
```

**Pull Request Filters** (optional):
* `authors` - List of GitHub usernames. Only show PRs from these users.
* `include_drafts` - Boolean. Include draft PRs if `true`.
* `title_regex` - Regex pattern. Only show PRs with matching titles.

#### Team Productivity Notifications
```json
{
    "notifications": [
        {
            "type": "team_productivity",
            "slack_channel": "team-metrics",
            "repositories": ["org/repo1", "org/repo2"],
            "team_members": ["dev1", "dev2", "dev3"],
            "time_window_days": 14
        }
    ]
}
```

**Team Productivity Options**:
* `team_members` - Required. List of GitHub usernames to track.
* `time_window_days` - Optional. Days to look back (defaults to 14).

**Productivity Metrics Included**:
- Total merged PRs by the team
- Total lines added/deleted by the team  
- Per-repository breakdown of merged PRs and line changes
- Individual approval counts (who reviewed the most PRs)

### How to run
Before you run the app, make sure you have already setup the `.env` file and the `config.json` file.
#### Directly from Docker Hub
The app is available as a Docker image [fmudrunek/github-slack-pr-notifier](https://hub.docker.com/r/fmudrunek/github-slack-pr-notifier) on Docker Hub so it can be run directly. Just mount a `config.json` into /app/resources in the container:

    # Run pull request notifications (default)
    docker run --rm --env-file ./.env -v ${pwd}/my_config.json:/app/resources/config.json:ro fmudrunek/github-slack-pr-notifier:latest
    
    # Run only productivity notifications
    docker run --rm --env-file ./.env -v ${pwd}/my_config.json:/app/resources/config.json:ro fmudrunek/github-slack-pr-notifier:latest --type team_productivity

#### Locally
##### Using Docker
Add your configuration to `/resources/config.json` and run the following commands:

    docker build -t pr_notifier .
    
    # Run pull request notifications (default)
    docker run --rm --env-file ./.env -v ${pwd}/resources/config.json:/app/resources/config.json:ro pr_notifier
    
    # Run only productivity notifications
    docker run --rm --env-file ./.env -v ${pwd}/resources/config.json:/app/resources/config.json:ro pr_notifier --type team_productivity

##### Using DockerCompose
For added convenience, a Docker Compose file is available to automatically build and run the container for you, using the configuration from the `.env` and `./resources/config.json` file.

    docker compose up

##### Using Python + Poetry
1. Follow the [Development](#development) section to set up your virtual environment and install dependencies.
2. Run the app. It will be looking into `./resources/config.json` for the configuration.

        # Run pull request notifications (default)
        poetry run python .\src\main.py
        
        # Run only pull request notifications
        poetry run python .\src\main.py --type pull_requests
        
        # Run only team productivity notifications
        poetry run python .\src\main.py --type team_productivity


### How to change the name, icon and description of the Slack bot
* Go to [Slack API - Apps](https://api.slack.com/apps), click on your app -> Basic Information -> Scroll down to Display Information.
* Change the name, icon and description. This is what will be displayed in the Slack channel when the bot posts a message.


## Development
For details on work with the code/project, how to run tests, formatters & how to to do maintenance work see the [Developer README.md](./src/notifier/README.md)
