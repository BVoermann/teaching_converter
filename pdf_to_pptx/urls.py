from django.contrib import admin
from django.contrib.staticfiles.views import serve as serve_static
from django.urls import path, re_path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('converter.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# The app is run with `manage.py runserver` in production too (see entrypoint.sh),
# which only serves STATIC_URL automatically when DEBUG=True. Serve it explicitly
# here so static assets (favicons, AI label images, etc.) work with DEBUG=False.
urlpatterns += [
    re_path(r'^static/(?P<path>.*)$', serve_static, {'insecure': True}),
]