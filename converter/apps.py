import os
import time
import threading
from django.apps import AppConfig
from django.conf import settings


def _periodic_cleanup():
    """Background thread that deletes files older than 30 minutes from the media directory."""
    max_age_seconds = 30 * 60  # 30 minutes
    interval = 10 * 60  # check every 10 minutes

    while True:
        time.sleep(interval)
        try:
            media_root = settings.MEDIA_ROOT
            if not os.path.isdir(media_root):
                continue
            now = time.time()
            for filename in os.listdir(media_root):
                filepath = os.path.join(media_root, filename)
                if os.path.isfile(filepath):
                    age = now - os.path.getmtime(filepath)
                    if age > max_age_seconds:
                        try:
                            os.remove(filepath)
                        except OSError:
                            pass
        except Exception:
            pass


class ConverterConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'converter'

    def ready(self):
        cleanup_thread = threading.Thread(target=_periodic_cleanup, daemon=True)
        cleanup_thread.start()
