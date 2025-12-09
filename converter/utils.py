from pdf2image import convert_from_path
from pptx import Presentation
from pptx.util import Inches
import os
import tempfile
import json
import zipfile
import base64
import subprocess
from PIL import Image


def pdf_to_pptx(pdf_path, output_path, progress_callback=None):

    # Convert PDF pages to images
    with tempfile.TemporaryDirectory() as temp_dir:
        images = convert_from_path(pdf_path, dpi=150)

        # Create PowerPoint presentation
        prs = Presentation()

        # Set slide dimensions (16:9 widescreen aspect ratio)
        prs.slide_width = Inches(10)
        prs.slide_height = Inches(5.625)

        total_pages = len(images)

        for i, image in enumerate(images):
            # Add blank slide
            blank_slide_layout = prs.slide_layouts[6]  # Blank layout
            slide = prs.slides.add_slide(blank_slide_layout)

            # Save image temporarily
            img_path = os.path.join(temp_dir, f'page_{i}.png')
            image.save(img_path, 'PNG')

            # Add image to slide (fit to slide)
            left = Inches(0)
            top = Inches(0)
            slide.shapes.add_picture(img_path, left, top,
                                     width=prs.slide_width,
                                     height=prs.slide_height)

            # Report progress
            if progress_callback:
                progress_callback(i + 1, total_pages)

        # Save presentation
        prs.save(output_path)

    return output_path


def pptx_to_images(pptx_path, output_dir, progress_callback=None):
    """
    Convert PPTX slides to images using LibreOffice and pdf2image

    Args:
        pptx_path: Path to PPTX file
        output_dir: Directory where images will be saved
        progress_callback: Optional callback for progress updates

    Returns:
        List of image file paths
    """
    image_paths = []

    with tempfile.TemporaryDirectory() as temp_pdf_dir:
        # Step 1: Convert PPTX to PDF using LibreOffice
        try:
            result = subprocess.run(
                ['soffice', '--headless', '--convert-to', 'pdf', '--outdir', temp_pdf_dir, pptx_path],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode != 0:
                raise Exception(f"LibreOffice conversion failed: {result.stderr}")

            # Find the generated PDF file
            pdf_filename = os.path.splitext(os.path.basename(pptx_path))[0] + '.pdf'
            pdf_path = os.path.join(temp_pdf_dir, pdf_filename)

            if not os.path.exists(pdf_path):
                raise Exception(f"PDF file not generated: {pdf_path}")

        except subprocess.TimeoutExpired:
            raise Exception("PPTX conversion timeout (exceeded 5 minutes)")
        except FileNotFoundError:
            raise Exception("LibreOffice (soffice) not found. Please ensure LibreOffice is installed.")
        except Exception as e:
            raise Exception(f"Error converting PPTX to PDF: {str(e)}")

        # Step 2: Convert PDF to images using pdf2image
        try:
            images = convert_from_path(pdf_path, dpi=150)
            total_slides = len(images)

            for i, image in enumerate(images):
                # Save each slide as an image
                img_filename = f'pptx_slide_{i}.png'
                img_path = os.path.join(output_dir, img_filename)
                image.save(img_path, 'PNG')
                image_paths.append(img_path)

                # Report progress
                if progress_callback:
                    progress_callback(i + 1, total_slides, 'Converting PPTX slides')

        except Exception as e:
            raise Exception(f"Error converting PDF to images: {str(e)}")

    return image_paths


def images_to_h5p(image_paths, output_path, content_type='presentation', alignment='middle', progress_callback=None):
    """
    Convert images to H5P format (Course Presentation or Interactive Book)

    Args:
        image_paths: List of paths to image files
        output_path: Path where the .h5p file will be saved
        content_type: 'presentation' or 'interactive-book'
        alignment: 'left', 'middle', 'right', or 'fullscreen'
        progress_callback: Optional callback function for progress updates
    """

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create H5P directory structure
        h5p_dir = os.path.join(temp_dir, 'h5p_content')
        os.makedirs(h5p_dir, exist_ok=True)

        content_dir = os.path.join(h5p_dir, 'content')
        os.makedirs(content_dir, exist_ok=True)

        images_dir = os.path.join(content_dir, 'images')
        os.makedirs(images_dir, exist_ok=True)

        total_images = len(image_paths)

        # Process and copy images
        image_files = []
        for i, img_path in enumerate(image_paths):
            # Open and resize if needed
            img = Image.open(img_path)
            img_filename = f'image_{i}.{img.format.lower() if img.format else "png"}'
            img_save_path = os.path.join(images_dir, img_filename)

            # Save image
            img.save(img_save_path)
            image_files.append({
                'filename': img_filename,
                'path': f'images/{img_filename}',
                'width': img.width,
                'height': img.height
            })

            if progress_callback:
                progress_callback(i + 1, total_images, 'Processing images')

        # Create content.json based on content type
        if content_type == 'presentation':
            content_json = create_presentation_content(image_files, alignment)
            library = 'H5P.CoursePresentation'
            major_version = 1
            minor_version = 25
            dependencies = [
                {"machineName": "H5P.CoursePresentation", "majorVersion": 1, "minorVersion": 25},
                {"machineName": "H5P.Image", "majorVersion": 1, "minorVersion": 1}
            ]
        else:
            content_json = create_interactive_book_content(image_files, alignment)
            library = 'H5P.InteractiveBook'
            major_version = 1
            minor_version = 8
            dependencies = [
                {"machineName": "H5P.InteractiveBook", "majorVersion": 1, "minorVersion": 8},
                {"machineName": "H5P.Column", "majorVersion": 1, "minorVersion": 16},
                {"machineName": "H5P.AdvancedText", "majorVersion": 1, "minorVersion": 1}
            ]

        # Write content.json
        with open(os.path.join(content_dir, 'content.json'), 'w', encoding='utf-8') as f:
            json.dump(content_json, f, indent=2)

        # Create h5p.json
        h5p_json = {
            "title": "Image Collection",
            "language": "en",
            "mainLibrary": library,
            "embedTypes": ["div"],
            "license": "U",
            "preloadedDependencies": dependencies
        }

        with open(os.path.join(h5p_dir, 'h5p.json'), 'w', encoding='utf-8') as f:
            json.dump(h5p_json, f, indent=2)

        # Create the H5P package (zip file)
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add h5p.json
            zipf.write(os.path.join(h5p_dir, 'h5p.json'), 'h5p.json')

            # Add content directory
            for root, dirs, files in os.walk(content_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, h5p_dir)
                    zipf.write(file_path, arcname)

        if progress_callback:
            progress_callback(total_images, total_images, 'H5P package created')

    return output_path


def create_presentation_content(image_files, alignment):
    """Create H5P Course Presentation content structure"""

    # Map alignment to H5P positioning
    alignment_map = {
        'left': {'x': 0, 'width': 50},
        'middle': {'x': 25, 'width': 50},
        'right': {'x': 50, 'width': 50},
        'fullscreen': {'x': 0, 'width': 100}
    }

    pos = alignment_map.get(alignment, alignment_map['middle'])

    slides = []
    for img_data in image_files:
        slide = {
            "elements": [
                {
                    "x": pos['x'],
                    "y": 10,
                    "width": pos['width'],
                    "height": 80,
                    "action": {
                        "library": "H5P.Image 1.1",
                        "params": {
                            "contentName": "Image",
                            "file": {
                                "path": img_data['path'],
                                "mime": f"image/{img_data['filename'].split('.')[-1]}",
                                "width": img_data['width'],
                                "height": img_data['height']
                            },
                            "alt": "Image"
                        },
                        "subContentId": f"image-{image_files.index(img_data)}"
                    }
                }
            ],
            "keywords": []
        }
        slides.append(slide)

    return {
        "presentation": {
            "slides": slides
        },
        "override": {
            "activeSurface": False,
            "hideSummarySlide": True,
            "summarySlideImage": None
        }
    }


def create_interactive_book_content(image_files, alignment):
    """Create H5P Interactive Book content structure"""

    # Map alignment to CSS text-align values
    alignment_css = {
        'left': 'left',
        'middle': 'center',
        'right': 'right',
        'fullscreen': 'center'
    }

    # Map alignment to image width
    alignment_width = {
        'left': '50%',
        'middle': '70%',
        'right': '50%',
        'fullscreen': '100%'
    }

    css_align = alignment_css.get(alignment, 'center')
    img_width = alignment_width.get(alignment, '70%')

    chapters = []
    for i, img_data in enumerate(image_files):
        # Create chapter with Column layout containing AdvancedText with image
        chapter = {
            "title": f"Image {i + 1}",
            "content": {
                "library": "H5P.Column 1.16",
                "params": {
                    "content": [
                        {
                            "content": {
                                "library": "H5P.AdvancedText 1.1",
                                "params": {
                                    "text": f'<p style="text-align: {css_align};"><img src="images/{img_data["filename"]}" alt="Image {i + 1}" style="width: {img_width}; height: auto; max-width: 100%;" /></p>'
                                },
                                "subContentId": f"text-{i}",
                                "metadata": {
                                    "contentType": "Text",
                                    "license": "U",
                                    "title": f"Image {i + 1}"
                                }
                            },
                            "useSeparator": "auto"
                        }
                    ]
                },
                "subContentId": f"column-{i}",
                "metadata": {
                    "contentType": "Column",
                    "license": "U",
                    "title": f"Chapter {i + 1}"
                }
            }
        }
        chapters.append(chapter)

    return {
        "bookCover": {
            "coverDescription": "Image collection as interactive book",
            "coverMedium": None,
            "coverAltText": ""
        },
        "chapters": chapters,
        "behaviour": {
            "defaultTableOfContents": True,
            "progressIndicators": True,
            "progressAuto": False,
            "displayTOC": True
        },
        "read": "Read",
        "displayTOC": "Display table of contents",
        "hideTOC": "Hide table of contents",
        "nextPage": "Next page",
        "previousPage": "Previous page",
        "navigationLabel": "Book navigation",
        "titleLabel": "Book title",
        "pagesLabel": "Pages",
        "pageLabel": "Page",
        "readspeakerProgress": "@pages of @total pages"
    }