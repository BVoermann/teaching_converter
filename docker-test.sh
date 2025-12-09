#!/bin/bash
# Docker setup test script

set -e

echo "=================================================="
echo "Testing Docker Setup for PDF to PPTX Converter"
echo "=================================================="

# Check if Docker is installed
echo ""
echo "1️⃣  Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi
echo "✅ Docker is installed: $(docker --version)"

# Check if Docker Compose is installed
echo ""
echo "2️⃣  Checking Docker Compose installation..."
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi
echo "✅ Docker Compose is installed: $(docker-compose --version)"

# Build the Docker image
echo ""
echo "3️⃣  Building Docker image..."
docker-compose build

# Start the container
echo ""
echo "4️⃣  Starting container..."
docker-compose up -d

# Wait for container to be ready
echo ""
echo "5️⃣  Waiting for application to start (30 seconds)..."
sleep 30

# Check if container is running
echo ""
echo "6️⃣  Checking container status..."
if docker-compose ps | grep -q "Up"; then
    echo "✅ Container is running"
else
    echo "❌ Container is not running"
    docker-compose logs
    exit 1
fi

# Test HTTP connection
echo ""
echo "7️⃣  Testing HTTP connection..."
if curl -f http://localhost:8000 > /dev/null 2>&1; then
    echo "✅ Application is responding on http://localhost:8000"
else
    echo "⚠️  Application might not be ready yet. Checking logs..."
    docker-compose logs --tail=20
fi

# Test LibreOffice installation
echo ""
echo "8️⃣  Testing LibreOffice installation..."
if docker-compose exec -T web soffice --version > /dev/null 2>&1; then
    echo "✅ LibreOffice is installed"
else
    echo "❌ LibreOffice is not installed correctly"
    exit 1
fi

# Show logs
echo ""
echo "=================================================="
echo "✅ Docker setup test completed!"
echo "=================================================="
echo ""
echo "Your application is running at: http://localhost:8000"
echo ""
echo "Useful commands:"
echo "  - View logs:        docker-compose logs -f"
echo "  - Stop container:   docker-compose down"
echo "  - Restart:          docker-compose restart"
echo "  - Access shell:     docker-compose exec web bash"
echo ""
echo "To stop the container, run: docker-compose down"
echo "=================================================="
