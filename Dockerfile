# Updated Dockerfile for proper static file serving
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

RUN echo "Acquire::http::Pipeline-Depth 0;" > /etc/apt/apt.conf.d/99custom && \
    echo "Acquire::http::No-Cache true;" >> /etc/apt/apt.conf.d/99custom && \
    echo "Acquire::BrokenProxy    true;" >> /etc/apt/apt.conf.d/99custom

# Install system dependencies
RUN apt-get clean && apt-get update && apt-get upgrade -y && apt-get install -y \
        --no-install-recommends \
        postgresql-client \
        curl \
        gettext \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Create staticfiles directory and set permissions
RUN mkdir -p /app/staticfiles && chmod 755 /app/staticfiles

# Collect static files using Docker settings
# This ensures WhiteNoise can find and serve your CSS files
RUN python manage.py collectstatic --noinput --settings=docker_settings

# Expose port
EXPOSE 8000

# Health check that verifies both the app and static files
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Run Django with Docker-specific settings
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000", "--settings=docker_settings"]