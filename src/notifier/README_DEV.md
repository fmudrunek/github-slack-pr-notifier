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