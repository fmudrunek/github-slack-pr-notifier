# Pull Requests Notifier
TODO:
* Short description
* Image of the bot in action


## How to use
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

### Configuration
See [config_example.json](./config_example.json)
```json
{
  "notifications": [
    {
      "slack_channel": "integration_test",
      "repositories": ["ipm/cdn", "ipm/cms"]
    },
    {
      "slack_channel": "U0J1LSZAL",
      "repositories": ["mamon/shepherd-cdn", "mamon/shepherd-cms", "mamon/mamba"]
    }
  ]
}

```
### Environment variables
See [.env.example](./.env.example)
```
GITHUB_BASE_URL=https://github.com
GITHUB_TOKEN=
SLACK_OAUTH_TOKEN=
PATH_TO_CONFIG=./config.json
```

### How to run
* Using DockerHub
* Locally
    * Using Docker
    * Using DockerCompose
    * Using Python + Poetry

### How to change the name, icon and description of the Slack bot
* Go to [Slack API - Apps](https://api.slack.com/apps), click on your app -> Basic Information -> Scroll down to Display Information.
* Change the name, icon and description. This is what will be displayed in the Slack channel when the bot posts a message.


Modifications/usages
How to run from Docker vs locally

Github REST api url - api. vs /api/v3.
    - Github token https://help.github.com/en/github/authenticating-to-github/creating-a-personal-access-token-for-the-command-line
    - TOKEN: No additional rights required