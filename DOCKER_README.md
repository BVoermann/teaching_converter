# Docker Setup for PDF to PPTX Converter

This document explains how to run the PDF to PPTX / Images to H5P converter application using Docker.

## Prerequisites

- Docker installed ([Get Docker](https://docs.docker.com/get-docker/))
- Docker Compose installed (usually comes with Docker Desktop)

## Quick Start

### 1. Build and Start the Container

```bash
docker-compose up --build
```

This will:
- Build the Docker image with all dependencies (Python, LibreOffice, poppler-utils)
- Start the Django application on port 8000
- Run database migrations automatically

### 2. Access the Application

Open your browser and navigate to:
```
http://localhost:8000
```

### 3. Stop the Container

Press `Ctrl+C` in the terminal, or run:
```bash
docker-compose down
```

---

## Docker Commands

### Build the image
```bash
docker-compose build
```

### Start in background (detached mode)
```bash
docker-compose up -d
```

### View logs
```bash
docker-compose logs -f
```

### Stop the container
```bash
docker-compose down
```

### Restart the container
```bash
docker-compose restart
```

### Access the container shell
```bash
docker-compose exec web bash
```

### Run Django management commands
```bash
# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Check for issues
docker-compose exec web python manage.py check
```

---

## File Persistence

The following directories/files are persisted using Docker volumes:

- **`./media/`** - Uploaded files and converted outputs
- **`./db.sqlite3`** - SQLite database
- **`.`** - Entire project directory (for development)

This means your data will persist even if you stop and restart the container.

---

## Environment Variables

You can customize the application by setting environment variables in `docker-compose.yml`:

```yaml
environment:
  - DJANGO_SETTINGS_MODULE=pdf_to_pptx.settings
  - PYTHONUNBUFFERED=1
  - DEBUG=True  # Set to False in production
```

---

## Production Deployment

For production, consider these changes:

### 1. Update Django Settings

Edit `pdf_to_pptx/settings.py`:
```python
DEBUG = False
ALLOWED_HOSTS = ['your-domain.com', 'localhost']
```

### 2. Use Production Server

Modify the `Dockerfile` entrypoint to use gunicorn instead of Django's development server:

```dockerfile
# Install gunicorn
RUN pip install gunicorn

# Update entrypoint
CMD ["gunicorn", "pdf_to_pptx.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### 3. Add Nginx Reverse Proxy (Optional)

Create an `nginx` service in `docker-compose.yml` to handle static files and reverse proxy.

---

## Troubleshooting

### LibreOffice Issues

If you encounter LibreOffice conversion errors:
```bash
# Access container shell
docker-compose exec web bash

# Test LibreOffice manually
soffice --headless --convert-to pdf --outdir /tmp /path/to/test.pptx
```

### Permission Issues

If you get permission errors with mounted volumes:
```bash
# Fix permissions
sudo chown -R $USER:$USER ./media ./db.sqlite3
```

### Port Already in Use

If port 8000 is already in use, change it in `docker-compose.yml`:
```yaml
ports:
  - "8080:8000"  # Change 8080 to any available port
```

---

## Development Workflow

The current setup mounts your local directory into the container, so:

1. **Code changes are reflected immediately** (no need to rebuild)
2. **Database and media files persist** across container restarts
3. **You can edit files locally** using your IDE

To disable live code sync (for production):
- Remove the volume mount `. : /app` from `docker-compose.yml`

---

## Architecture

```
┌─────────────────────────────────────┐
│     Docker Container (web)          │
│                                     │
│  ┌──────────────────────────────┐  │
│  │   Django Application         │  │
│  │   (Port 8000)                │  │
│  └──────────────────────────────┘  │
│                                     │
│  ┌──────────────────────────────┐  │
│  │   LibreOffice (Headless)     │  │
│  │   - PPTX → PDF conversion    │  │
│  └──────────────────────────────┘  │
│                                     │
│  ┌──────────────────────────────┐  │
│  │   pdf2image / Poppler        │  │
│  │   - PDF → Images conversion  │  │
│  └──────────────────────────────┘  │
│                                     │
│  ┌──────────────────────────────┐  │
│  │   SQLite Database            │  │
│  └──────────────────────────────┘  │
│                                     │
└─────────────────────────────────────┘
         │
         ├─── Volume: ./media
         ├─── Volume: ./db.sqlite3
         └─── Port: 8000 → localhost:8000
```

---

## What's Included

The Docker image includes:

- **Python 3.12** - Application runtime
- **Django 5.2.8** - Web framework
- **LibreOffice** - For PPTX to PDF conversion
- **Poppler Utils** - For PDF to images conversion
- **Pillow** - Image processing
- **All Python dependencies** from `requirements.txt`

---

## Support

For issues or questions:
1. Check the logs: `docker-compose logs -f`
2. Access the shell: `docker-compose exec web bash`
3. Run diagnostics: `docker-compose exec web python manage.py check`

---

## Summary

```bash
# Start everything
docker-compose up --build

# Access app
http://localhost:8000

# Stop everything
docker-compose down
```

That's it! Your PDF to PPTX / Images to H5P converter is now running in Docker! 🐳
