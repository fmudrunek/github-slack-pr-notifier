# Pull Requests Notifier
Short description





required env. variables
see [.env.example](./.env.example)
GITHUB_BASE_URL=https://github.com
GITHUB_TOKEN=
SLACK_BEARER_TOKEN=
PATH_TO_CONFIG=./config.json
TODO: add how-to-get and required permissions


config.json
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

Modifications/usages
How to run from Docker vs locally

Github REST api url - api. vs /api/v3.
    - Github token https://help.github.com/en/github/authenticating-to-github/creating-a-personal-access-token-for-the-command-line
    - TOKEN: No additional rights required