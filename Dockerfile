# Use Python 3.12 base image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # LibreOffice for PPTX to PDF conversion
    libreoffice \
    libreoffice-writer \
    libreoffice-calc \
    libreoffice-impress \
    # Poppler utils for pdf2image
    poppler-utils \
    # Image processing libraries
    libjpeg-dev \
    libpng-dev \
    # FFmpeg for video/audio compression
    ffmpeg \
    # Other useful tools
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . /app/

# Create media directory for file uploads
RUN mkdir -p /app/media

# Create directory for LibreOffice user profile (fixes headless mode issues)
RUN mkdir -p /tmp/libreoffice

# Collect static files (if needed)
RUN python manage.py collectstatic --noinput || echo "No static files to collect"

# Expose port 8000
EXPOSE 8000

# Create entrypoint script
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# Run migrations\n\
echo "Running database migrations..."\n\
python manage.py migrate --noinput\n\
\n\
# Create superuser if it does not exist (optional)\n\
# python manage.py createsuperuser --noinput --username admin --email admin@example.com || true\n\
\n\
# Start Django development server\n\
echo "Starting Django development server..."\n\
python manage.py runserver 0.0.0.0:8000\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
