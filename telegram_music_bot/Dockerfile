FROM python:3.11-slim-bookworm

# Set environment variables
ENV PYTHONUNBUFFERED 1
ENV APP_HOME /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
        git \
        # For yt-dlp to work properly, some dependencies might be needed
        # Check yt-dlp documentation for minimal requirements
        # For example, ca-certificates, openssl, etc.
        ca-certificates \
        openssl \
    && rm -rf /var/lib/apt/lists/*

# Install yt-dlp
RUN pip install yt-dlp

# Create app directory
WORKDIR $APP_HOME

# Copy project files
COPY pyproject.toml $APP_HOME/
COPY src/ $APP_HOME/src/

# Install Python dependencies from pyproject.toml
RUN pip install poetry && poetry install --no-root --no-dev

# Expose port for potential webhooks (if used, though this is a bot)
# EXPOSE 80

# Command to run the bot
CMD ["python", "src/main.py"]
