from django.shortcuts import render
from django.http import FileResponse, HttpResponse, JsonResponse
from django.core.files.storage import FileSystemStorage
from django.views.decorators.csrf import csrf_exempt
from .utils import pdf_to_pptx, images_to_h5p
import os
import uuid
import threading

# Global dictionary to track conversion progress
conversion_progress = {}
h5p_conversion_progress = {}


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
                'output_path': output_path
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
                        # Remove from progress dict
                        if task_id in conversion_progress:
                            del conversion_progress[task_id]
                    except:
                        pass

                threading.Thread(target=cleanup).start()

                return response

    return HttpResponse('File not found', status=404)


def upload_images_to_h5p(request):
    if request.method == 'POST' and request.FILES.getlist('image_files'):
        image_files = request.FILES.getlist('image_files')
        content_type = request.POST.get('content_type', 'presentation')
        alignment = request.POST.get('alignment', 'middle')

        # Generate unique task ID
        task_id = str(uuid.uuid4())
        h5p_conversion_progress[task_id] = {'status': 'uploading', 'progress': 0, 'message': 'Uploading images...'}

        # Save uploaded images
        fs = FileSystemStorage()
        image_paths = []

        for image_file in image_files:
            filename = fs.save(image_file.name, image_file)
            image_paths.append(fs.path(filename))

        # Create output filename
        output_filename = f'h5p_content_{task_id}.h5p'
        output_path = fs.path(output_filename)

        h5p_conversion_progress[task_id] = {'status': 'converting', 'progress': 10, 'message': 'Starting conversion...'}

        try:
            # Convert images to H5P with progress callback
            def progress_callback(current, total, message='Processing'):
                progress = 10 + int((current / total) * 80)
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
                'output_path': output_path
            }

            # Clean up uploaded images
            for img_path in image_paths:
                if os.path.exists(img_path):
                    try:
                        os.remove(img_path)
                    except:
                        pass

            return JsonResponse({'task_id': task_id})

        except Exception as e:
            # Clean up on error
            for img_path in image_paths:
                if os.path.exists(img_path):
                    try:
                        os.remove(img_path)
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
                        # Remove from progress dict
                        if task_id in h5p_conversion_progress:
                            del h5p_conversion_progress[task_id]
                    except:
                        pass

                threading.Thread(target=cleanup).start()

                return response

    return HttpResponse('File not found', status=404)