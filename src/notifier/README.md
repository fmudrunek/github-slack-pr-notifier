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
Quality checks are split into focused tasks using [Poe](https://github.com/nat-n/poethepoet):

| Command | What it does |
|---|---|
| `poetry run poe check` | Run all checks: type checking → linting → tests |
| `poetry run poe test` | Run tests only (fast iteration) |
| `poetry run poe type` | Run mypy type checking only |
| `poetry run poe lint` | Run pylint only |

Each tool exits non-zero on failure; `poe check` stops at the first failing step.

### Code formatting
The application is formatted using [black](https://black.readthedocs.io/en/stable/) and [isort](https://pycqa.github.io/isort/).  
You can either run black and isort manually or use prepared [Poe](https://github.com/nat-n/poethepoet) task to format the whole project.

	$ poetry run poe format-code

### Running locally via Claude Code
If you use [Claude Code](https://claude.com/claude-code), the repo ships a `/run-notifier` skill (see [.claude/skills/run-notifier/](../../.claude/skills/run-notifier/SKILL.md)). It prompts for the flow (`pull_requests` / `team_productivity`), a config from `resources/`, and a `.env` file, shows the target Slack channel and final command, then runs the Docker build+run for you.

### Maintainance
To update dependencies within the pinned range, run:

    poetry update

To show dependency updates outside the pinned range:

    poetry show --outdated --top-level