# PDF to PPTX Converter

A Django web application for converting PDF files to PowerPoint presentations and creating H5P interactive content packages.

## Features

- Convert PDF files to PPTX format
- Convert images to H5P packages
- Convert PPTX files to H5P packages
- Real-time conversion progress tracking
- Support for multiple content types (presentations, course presentations)

## Requirements

- Python 3.12+
- See `requirements.txt` for Python dependencies

## Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run migrations:
   ```bash
   python manage.py migrate
   ```
5. Start the development server:
   ```bash
   python manage.py runserver
   ```

## Usage

Access the application at `http://localhost:8000`

- Upload a PDF file to convert it to PPTX
- Upload images or PPTX files to create H5P packages

## Docker

See [DOCKER_README.md](DOCKER_README.md) for Docker setup instructions.

## Project Structure

- `converter/` - Main application containing conversion logic
- `pdf_to_pptx/` - Django project settings
- `media/` - Uploaded and converted files
