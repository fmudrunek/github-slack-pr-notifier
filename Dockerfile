# The builder image, used to build the virtual environment
FROM python:3.12-bookworm as builder

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN pip install --no-cache-dir poetry==1.7.0 && \
    poetry install --without dev --no-root && \
    rm -rf $POETRY_CACHE_DIR

# The runtime image, used to just run the code provided its virtual environment
FROM python:3.12-slim-bookworm as runtime

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    # do not buffer output to stdout
    PYTHONUNBUFFERED=1 \
    # prevents python creating .pyc files
    PYTHONDONTWRITEBYTECODE=1


COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

COPY ./src /app/src/

# Set the PYTHONPATH environment variable so it finds the main module
ENV PYTHONPATH=/app/src

WORKDIR app/src/

ENTRYPOINT ["python", "-m", "main"]