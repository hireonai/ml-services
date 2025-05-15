FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Set Python to run in unbuffered mode
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create credentials directory
RUN mkdir -p credentials

# Install dependencies first (for better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user for security
RUN adduser --disabled-password --gecos "" appuser

# Copy application code
COPY ./app ./app
COPY main.py .

# Copy only necessary files (avoid .env)
COPY .env.example ./.env.example

# Set permissions
RUN chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]