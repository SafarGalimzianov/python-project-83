# Use the official Python image from the Docker Hub
FROM python:3.12-slim

# Update the package list and install make gcc and libpq-dev (for postgresql) and remove the package list (cached files created by apt-get update)
RUN apt update && apt install -yq make build-essential gcc libpq-dev && apt clean && rm -rf /var/lib/apt/lists/*

# Create a non-root user and group
RUN groupadd -r appuser && useradd --no-log-init -r -g appuser appuser

# Create the home directory for appuser and ensure permissions
RUN mkdir -p /home/appuser && chown -R appuser:appuser /home/appuser

# Set the working directory in the container
WORKDIR /app

# Switch to the non-root user
USER appuser

# Install Poetry without root permissions
RUN pip install poetry

# Add the local bin directory to PATH
ENV PATH="$PATH:/home/appuser/.local/bin"

# Copy the pyproject.toml and poetry.lock files from the current directory to the container ./
COPY pyproject.toml poetry.lock ./

# Install dependencies without installing the whole project
RUN poetry install --no-root

# Copy the rest of the application code from the host . to the container .
COPY . .

# Set environment variables
ENV FLASK_APP=page_analyzer.app:app
ENV FLASK_RUN_HOST=0.0.0.0

# No need to expose the port the app runs on
# Render handles the port assignment dynamically

# Run the application inside shell to use the environment variable $PORT provided by Render
CMD ["sh", "-c", "poetry run gunicorn --bind=0.0.0.0:$PORT page_analyzer.app:app"]