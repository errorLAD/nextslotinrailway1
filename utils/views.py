from django.http import Http404, HttpResponse
from .models import DatabaseFile


def serve_db_file(request, name):
    """Serve a file stored in the DatabaseFile model.

    This view is used by the custom DatabaseStorage backend to return
    files stored in PostgreSQL.
    """
    try:
        db_file = DatabaseFile.objects.get(name=name)
    except DatabaseFile.DoesNotExist:
        raise Http404("File not found")

    # Ensure binary content and correct content type
    content = bytes(db_file.data)
    response = HttpResponse(content, content_type=db_file.content_type or "application/octet-stream")
    if db_file.size:
        response["Content-Length"] = db_file.size
    return response
