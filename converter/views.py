from django.shortcuts import render
from django.http import FileResponse, HttpResponse, JsonResponse
from django.core.files.storage import FileSystemStorage
from django.views.decorators.csrf import csrf_exempt
from .utils import pdf_to_pptx, images_to_h5p, pptx_to_images, compress_files, get_file_type
import os
import uuid
import threading
import tempfile
import shutil

# Global dictionary to track conversion progress
conversion_progress = {}
h5p_conversion_progress = {}
compress_conversion_progress = {}


def upload_pdf(request):
    if request.method == 'POST' and request.FILES.get('pdf_file'):
        pdf_file = request.FILES['pdf_file']

        # Generate unique task ID
        task_id = str(uuid.uuid4())
        conversion_progress[task_id] = {'status': 'uploading', 'progress': 0, 'message': 'Uploading file...'}

        # Save uploaded PDF
        fs = FileSystemStorage()
        pdf_filename = fs.save(pdf_file.name, pdf_file)
        pdf_path = fs.path(pdf_filename)

        # Create output filename
        output_filename = pdf_filename.replace('.pdf', '.pptx')
        output_path = fs.path(output_filename)

        conversion_progress[task_id] = {'status': 'converting', 'progress': 10, 'message': 'Starting conversion...'}

        try:
            # Convert PDF to PPTX with progress callback
            def progress_callback(current, total):
                progress = 10 + int((current / total) * 80)
                conversion_progress[task_id] = {
                    'status': 'converting',
                    'progress': progress,
                    'message': f'Converting page {current} of {total}...'
                }

            pdf_to_pptx(pdf_path, output_path, progress_callback)

            conversion_progress[task_id] = {
                'status': 'complete',
                'progress': 100,
                'message': 'Conversion complete!',
                'output_filename': output_filename,
                'output_path': output_path,
                'pdf_path': pdf_path
            }

            # Return task ID for client to poll
            return JsonResponse({'task_id': task_id})

        except Exception as e:
            # Clean up on error
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
            conversion_progress[task_id] = {
                'status': 'error',
                'progress': 0,
                'message': f'Error: {str(e)}'
            }
            return JsonResponse({'task_id': task_id, 'error': str(e)}, status=500)

    return render(request, 'converter/upload.html')


def check_progress(request, task_id):
    """Endpoint to check conversion progress"""
    if task_id in conversion_progress:
        return JsonResponse(conversion_progress[task_id])
    return JsonResponse({'status': 'not_found', 'message': 'Task not found'}, status=404)


def download_file(request, task_id):
    """Endpoint to download the converted file"""
    if task_id in conversion_progress:
        progress_data = conversion_progress[task_id]
        if progress_data['status'] == 'complete':
            output_path = progress_data['output_path']
            output_filename = progress_data['output_filename']

            if os.path.exists(output_path):
                response = FileResponse(
                    open(output_path, 'rb'),
                    content_type='application/vnd.openxmlformats-officedocument.presentationml.presentation'
                )
                response['Content-Disposition'] = f'attachment; filename="{output_filename}"'

                # Clean up files after a short delay
                def cleanup():
                    import time
                    time.sleep(5)
                    try:
                        if os.path.exists(output_path):
                            os.remove(output_path)
                        # Delete original PDF file
                        pdf_path = progress_data.get('pdf_path')
                        if pdf_path and os.path.exists(pdf_path):
                            os.remove(pdf_path)
                        # Remove from progress dict
                        if task_id in conversion_progress:
                            del conversion_progress[task_id]
                    except:
                        pass

                threading.Thread(target=cleanup).start()

                return response

    return HttpResponse('PPTX file not found', status=404)


def upload_images_to_h5p(request):
    if request.method == 'POST' and request.FILES.getlist('image_files'):
        image_files = request.FILES.getlist('image_files')
        content_type = request.POST.get('content_type', 'presentation')
        alignment = request.POST.get('alignment', 'middle')

        # Generate unique task ID
        task_id = str(uuid.uuid4())
        h5p_conversion_progress[task_id] = {'status': 'uploading', 'progress': 0, 'message': 'Uploading files...'}

        # Separate PPTX files from image files
        pptx_files = []
        regular_images = []

        for file in image_files:
            is_pptx = (
                file.name.lower().endswith('.pptx') or
                file.content_type == 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
            )
            if is_pptx:
                pptx_files.append(file)
            else:
                regular_images.append(file)

        # Save uploaded images
        fs = FileSystemStorage()
        image_paths = []
        temp_dirs = []  # Track temp directories for cleanup

        # Process PPTX files to extract slide images
        if pptx_files:
            total_pptx = len(pptx_files)
            for idx, pptx_file in enumerate(pptx_files):
                h5p_conversion_progress[task_id] = {
                    'status': 'converting',
                    'progress': 10 + int((idx / total_pptx) * 30),
                    'message': f'Converting PPTX {idx + 1} of {total_pptx}...'
                }

                # Save PPTX temporarily
                pptx_filename = fs.save(pptx_file.name, pptx_file)
                pptx_path = fs.path(pptx_filename)

                try:
                    # Create temp dir for converted images
                    temp_images_dir = tempfile.mkdtemp()
                    temp_dirs.append(temp_images_dir)

                    # Convert PPTX to images
                    slide_images = pptx_to_images(pptx_path, temp_images_dir)
                    image_paths.extend(slide_images)

                    # Cleanup PPTX file
                    os.remove(pptx_path)
                except Exception as e:
                    # Log error but continue with other files
                    print(f"Error converting {pptx_file.name}: {str(e)}")
                    if os.path.exists(pptx_path):
                        os.remove(pptx_path)

        # Save regular uploaded images
        for image_file in regular_images:
            filename = fs.save(image_file.name, image_file)
            image_paths.append(fs.path(filename))

        # Create output filename
        output_filename = f'h5p_content_{task_id}.h5p'
        output_path = fs.path(output_filename)

        h5p_conversion_progress[task_id] = {'status': 'converting', 'progress': 40, 'message': 'Creating H5P package...'}

        try:
            # Convert images to H5P with progress callback
            def progress_callback(current, total, message='Processing'):
                # Adjust progress: 40-90% for H5P conversion
                progress = 40 + int((current / total) * 50)
                h5p_conversion_progress[task_id] = {
                    'status': 'converting',
                    'progress': progress,
                    'message': f'{message} {current} of {total}...'
                }

            images_to_h5p(image_paths, output_path, content_type, alignment, progress_callback)

            h5p_conversion_progress[task_id] = {
                'status': 'complete',
                'progress': 100,
                'message': 'Conversion complete!',
                'output_filename': output_filename,
                'output_path': output_path,
                'image_paths': image_paths,
                'temp_dirs': temp_dirs
            }

            return JsonResponse({'task_id': task_id})

        except Exception as e:
            # Clean up on error
            for img_path in image_paths:
                if os.path.exists(img_path):
                    try:
                        os.remove(img_path)
                    except:
                        pass

            # Clean up temporary directories
            for temp_dir in temp_dirs:
                if os.path.exists(temp_dir):
                    try:
                        shutil.rmtree(temp_dir)
                    except:
                        pass

            h5p_conversion_progress[task_id] = {
                'status': 'error',
                'progress': 0,
                'message': f'Error: {str(e)}'
            }
            return JsonResponse({'task_id': task_id, 'error': str(e)}, status=500)

    return render(request, 'converter/upload.html')


def check_h5p_progress(request, task_id):
    """Endpoint to check H5P conversion progress"""
    if task_id in h5p_conversion_progress:
        return JsonResponse(h5p_conversion_progress[task_id])
    return JsonResponse({'status': 'not_found', 'message': 'Task not found'}, status=404)


def download_h5p_file(request, task_id):
    """Endpoint to download the converted H5P file"""
    if task_id in h5p_conversion_progress:
        progress_data = h5p_conversion_progress[task_id]
        if progress_data['status'] == 'complete':
            output_path = progress_data['output_path']
            output_filename = progress_data['output_filename']

            if os.path.exists(output_path):
                response = FileResponse(
                    open(output_path, 'rb'),
                    content_type='application/zip'
                )
                response['Content-Disposition'] = f'attachment; filename="{output_filename}"'

                # Clean up files after a short delay
                def cleanup():
                    import time
                    time.sleep(5)
                    try:
                        if os.path.exists(output_path):
                            os.remove(output_path)
                        # Clean up uploaded images
                        image_paths = progress_data.get('image_paths', [])
                        for img_path in image_paths:
                            if os.path.exists(img_path):
                                try:
                                    os.remove(img_path)
                                except:
                                    pass
                        # Clean up temporary directories
                        temp_dirs = progress_data.get('temp_dirs', [])
                        for temp_dir in temp_dirs:
                            if os.path.exists(temp_dir):
                                try:
                                    shutil.rmtree(temp_dir)
                                except:
                                    pass
                        # Remove from progress dict
                        if task_id in h5p_conversion_progress:
                            del h5p_conversion_progress[task_id]
                    except:
                        pass

                threading.Thread(target=cleanup).start()

                return response

    return HttpResponse('H5P file not found', status=404)


def upload_compress(request):
    if request.method == 'POST' and request.FILES.getlist('compress_files'):
        uploaded_files = request.FILES.getlist('compress_files')

        # Generate unique task ID
        task_id = str(uuid.uuid4())
        compress_conversion_progress[task_id] = {'status': 'uploading', 'progress': 0, 'message': 'Uploading files...'}

        # Save uploaded files and filter to supported types
        fs = FileSystemStorage()
        file_paths = []

        for f in uploaded_files:
            if get_file_type(f.name) is not None:
                filename = fs.save(f.name, f)
                file_paths.append(fs.path(filename))

        if not file_paths:
            compress_conversion_progress[task_id] = {
                'status': 'error',
                'progress': 0,
                'message': 'No supported files found. Please upload images, videos, or audio files.'
            }
            return JsonResponse({'task_id': task_id, 'error': 'No supported files'}, status=400)

        # Create output filename
        output_filename = f'compressed_{task_id}.zip'
        output_path = fs.path(output_filename)

        compress_conversion_progress[task_id] = {'status': 'converting', 'progress': 10, 'message': 'Starting compression...'}

        try:
            def progress_callback(current, total):
                progress = 10 + int((current / total) * 80)
                compress_conversion_progress[task_id] = {
                    'status': 'converting',
                    'progress': progress,
                    'message': f'Compressing file {current} of {total}...'
                }

            compress_files(file_paths, output_path, progress_callback)

            compress_conversion_progress[task_id] = {
                'status': 'complete',
                'progress': 100,
                'message': 'Compression complete!',
                'output_filename': output_filename,
                'output_path': output_path,
                'file_paths': file_paths
            }

            return JsonResponse({'task_id': task_id})

        except Exception as e:
            for path in file_paths:
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except:
                        pass

            compress_conversion_progress[task_id] = {
                'status': 'error',
                'progress': 0,
                'message': f'Error: {str(e)}'
            }
            return JsonResponse({'task_id': task_id, 'error': str(e)}, status=500)

    return render(request, 'converter/upload.html')


def check_compress_progress(request, task_id):
    if task_id in compress_conversion_progress:
        return JsonResponse(compress_conversion_progress[task_id])
    return JsonResponse({'status': 'not_found', 'message': 'Task not found'}, status=404)


def download_compress_file(request, task_id):
    if task_id in compress_conversion_progress:
        progress_data = compress_conversion_progress[task_id]
        if progress_data['status'] == 'complete':
            output_path = progress_data['output_path']
            output_filename = progress_data['output_filename']

            if os.path.exists(output_path):
                response = FileResponse(
                    open(output_path, 'rb'),
                    content_type='application/zip'
                )
                response['Content-Disposition'] = f'attachment; filename="{output_filename}"'

                def cleanup():
                    import time
                    time.sleep(5)
                    try:
                        if os.path.exists(output_path):
                            os.remove(output_path)
                        for path in progress_data.get('file_paths', []):
                            if os.path.exists(path):
                                try:
                                    os.remove(path)
                                except:
                                    pass
                        if task_id in compress_conversion_progress:
                            del compress_conversion_progress[task_id]
                    except:
                        pass

                threading.Thread(target=cleanup).start()

                return response

    return HttpResponse('File not found', status=404)