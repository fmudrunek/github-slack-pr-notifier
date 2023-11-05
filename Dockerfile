# The builder image, used to build the virtual environment
FROM python:3.12-bookworm as builder

RUN pip install poetry==1.7.0

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry install --without dev --no-root && rm -rf $POETRY_CACHE_DIR

# The runtime image, used to just run the code provided its virtual environment
FROM python:3.12-slim-bookworm as runtime

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

# do not buffer output to stdout
ENV PYTHONUNBUFFERED=1 \
    # prevents python creating .pyc files
    PYTHONDONTWRITEBYTECODE=1

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

COPY ./src/notifier /app/src/notifier

WORKDIR app/src/notifier

ENTRYPOINT ["python", "-m", "main"]