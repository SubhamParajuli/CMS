import mimetypes
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404
from django.utils._os import safe_join


def serve_production_media(request, path):
    file_path = Path(safe_join(str(settings.MEDIA_ROOT), path))
    if not file_path.is_file():
        raise Http404('Media file not found.')

    content_type, _ = mimetypes.guess_type(str(file_path))
    response = FileResponse(file_path.open('rb'), content_type=content_type)
    response['Cache-Control'] = 'public, max-age=86400'
    return response