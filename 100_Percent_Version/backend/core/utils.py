"""Chhoto helper function - notify(), audit(), paginate(), csv_safe(), serve_file()."""
import mimetypes
import os
import re

from django.core.paginator import Paginator
from django.http import FileResponse, Http404, HttpResponse, StreamingHttpResponse

from .models import AuditLog, Notification


def notify(user, message, url=""):
    """User ke ekta in-app notification pathay. user None hole kichu kore na."""
    if user is None:
        return None
    return Notification.objects.create(user=user, message=message[:255], url=url[:255])


def notify_many(users, message, url=""):
    for user in {u.pk: u for u in users if u is not None}.values():
        notify(user, message, url)


def audit(actor, action, detail=""):
    """Admin/HR er gurutwopurno kaj record kore."""
    name = ""
    if actor is not None and getattr(actor, "is_authenticated", False):
        name = actor.display_name
    else:
        actor = None
    return AuditLog.objects.create(actor=actor, actor_name=name, action=action[:60], detail=detail[:255])


def paginate(request, queryset, per_page=10):
    """Page object return kore. Page object ke template e list er moto loop kora jay."""
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(request.GET.get("page"))


def csv_safe(value):
    """Excel formula injection thekay: = + - @ diye shuru hole age ' boshay."""
    text = "" if value is None else str(value)
    if text[:1] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + text
    return text


_RANGE_RE = re.compile(r"bytes=(\d*)-(\d*)")


def serve_file(request, fieldfile, as_attachment=False):
    """
    Protected file download. File sorasori /media/ e khola thake na - permission check kore ei function diye dey.
    Video seek korar jonno HTTP Range support-o ache.
    """
    if not fieldfile or not fieldfile.name:
        raise Http404("No file")
    try:
        path = fieldfile.path
    except Exception:  # pragma: no cover
        raise Http404("No file")
    if not os.path.exists(path):
        raise Http404("File missing")
    content_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
    size = os.path.getsize(path)
    filename = os.path.basename(path)
    match = _RANGE_RE.match(request.headers.get("Range", ""))
    if match and not as_attachment:
        start_s, end_s = match.groups()
        if start_s == "" and end_s == "":
            match = None
        else:
            if start_s == "":  # suffix range
                length = int(end_s)
                start, end = max(size - length, 0), size - 1
            else:
                start = int(start_s)
                end = int(end_s) if end_s else size - 1
            end = min(end, size - 1)
            if start > end or start >= size:
                response = HttpResponse(status=416)
                response["Content-Range"] = f"bytes */{size}"
                return response

            def chunks():
                with open(path, "rb") as fh:
                    fh.seek(start)
                    remaining = end - start + 1
                    while remaining > 0:
                        data = fh.read(min(64 * 1024, remaining))
                        if not data:
                            break
                        remaining -= len(data)
                        yield data

            response = StreamingHttpResponse(chunks(), status=206, content_type=content_type)
            response["Content-Range"] = f"bytes {start}-{end}/{size}"
            response["Content-Length"] = str(end - start + 1)
            response["Accept-Ranges"] = "bytes"
            response["X-Content-Type-Options"] = "nosniff"
            return response
    response = FileResponse(open(path, "rb"), content_type=content_type, as_attachment=as_attachment, filename=filename)
    response["Accept-Ranges"] = "bytes"
    response["X-Content-Type-Options"] = "nosniff"
    return response
