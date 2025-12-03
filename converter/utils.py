from pdf2image import convert_from_path
from pptx import Presentation
from pptx.util import Inches
import os
import tempfile


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