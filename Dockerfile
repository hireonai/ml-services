FROM python:3.12.3-slim

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Set Python to run in unbuffered mode
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies and WeasyPrint dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    python3-dev \
    python3-setuptools \
    python3-wheel \
    python3-cffi \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    fonts-dejavu \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Create credentials directory
RUN mkdir -p credentials
COPY credentials/ ./credentials

# Copy .env file
COPY .env .

# Copy requirements or project files
COPY pyproject.toml ./
COPY ./app ./app
COPY main.py .

# Install dependencies using uv
RUN uv sync

# Create non-root user for security
RUN adduser --disabled-password --gecos "" appuser

# Set permissions
RUN chown -R appuser:appuser /app
USER appuser

# Run the application with PORT environment variable
CMD ["sh", "-c", "/app/.venv/bin/uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080} --reload"]