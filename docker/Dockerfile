# Multi-stage Dockerfile for API Conference Agent
# Stage 1: Base image with all dependencies
FROM python:3.10-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV POETRY_VERSION=2.1.4
ENV POETRY_HOME=/opt/poetry
ENV POETRY_NO_INTERACTION=1
ENV POETRY_VIRTUALENVS_IN_PROJECT=true
ENV POETRY_CACHE_DIR=/tmp/poetry_cache
ENV PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring
ENV PATH="$POETRY_HOME/bin:$PATH"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Set working directory
WORKDIR /app

# Copy Poetry configuration files
COPY pyproject.toml poetry.lock* README.md ./

# Install all dependencies (including dev dependencies for now)
RUN poetry install --no-interaction --no-ansi --no-root

# Copy application code
COPY app/ ./app/
COPY main.py .
COPY data/ ./data/
COPY scripts/ ./scripts/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Add the app directory to the Python path
ENV PYTHONPATH="${PYTHONPATH}:/app"

# Stage 2: Backend service
FROM base as backend

# Expose the port the app runs on
EXPOSE 8000

# Make entrypoint script executable
RUN chmod +x /app/scripts/docker-entrypoint.sh

# Use entrypoint script that handles DB initialization
ENTRYPOINT ["/app/scripts/docker-entrypoint.sh"]

# Stage 3: CSV Updater service
FROM base as csv-updater

# Create logs directory
RUN mkdir -p /app/logs

# Make the update script executable
RUN chmod +x /app/scripts/run_csv_update.sh

# Create cron job file
RUN echo "0 6 * * * /app/scripts/run_csv_update.sh >> /app/logs/cron.log 2>&1" > /etc/cron.d/csv-update

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/csv-update

# Apply cron job
RUN crontab /etc/cron.d/csv-update

# Create the log file to be able to run tail
RUN touch /app/logs/cron.log

# Run cron
CMD ["cron", "-f"] 