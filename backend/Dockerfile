# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies and Poetry
RUN apt-get update \
    && apt-get install -y curl build-essential libpq-dev \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Ensure that Poetry is in the PATH
ENV PATH="/root/.local/bin:$PATH"

# Copy only dependency definitions first for Docker cache
COPY pyproject.toml poetry.lock /app/

# Install all dependencies, including dev extras for reload
RUN poetry install --no-root --with dev

# Copy the rest of the application code
COPY . /app

# Expose the port your app runs on
EXPOSE 8232

# Default command with live-reload enabled
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8232", "--reload"]
