FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    nodejs \
    npm \
    yarn \
    libpq-dev \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Copy project files
COPY . .

# Install Node.js dependencies and build React apps
RUN cd marketing_front && npm install --legacy-peer-deps && npm run build
#RUN cd frontend && npm install && yarn build

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port for the application
EXPOSE 8000

# Use a non-root user for security
RUN useradd -m appuser
RUN chown -R appuser:appuser /app
USER appuser

# Set entrypoint script as executable
RUN chmod +x docker-entrypoint.sh

# Use entrypoint script
ENTRYPOINT ["/app/docker-entrypoint.sh"]