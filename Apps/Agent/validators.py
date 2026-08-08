import os
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# Dangerous extensions and MIME types that could cause XSS or code execution
DANGEROUS_EXTENSIONS = {
    '.html', '.htm', '.xhtml', '.shtml', '.svg', '.js', '.jsx', '.ts', '.tsx',
    '.php', '.php3', '.php4', '.php5', '.phtml', '.py', '.rb', '.pl', '.cgi',
    '.sh', '.bash', '.exe', '.bat', '.cmd', '.vbs', '.jar', '.msi', '.dll',
    '.asp', '.aspx', '.jsp', '.jspx', '.htc', '.swf'
}

DANGEROUS_MIME_TYPES = {
    'text/html', 'text/javascript', 'application/javascript', 'application/x-javascript',
    'image/svg+xml', 'application/x-php', 'application/x-httpd-php',
    'application/x-executable', 'application/x-msdownload', 'application/x-sh'
}

ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
ALLOWED_DOCUMENT_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.webp'}
ALLOWED_VIDEO_EXTENSIONS = {'.mp4', '.webm'}


def validate_file_upload(file_obj, allowed_extensions, max_size_mb=10, label="File"):
    """
    Validates an uploaded file for:
    1. Size limit (max_size_mb)
    2. Extension against allowed whitelist and dangerous blacklist
    3. Basic MIME type and file header integrity checks
    """
    if not file_obj:
        return

    # 1. File Size Check
    max_bytes = max_size_mb * 1024 * 1024
    if file_obj.size > max_bytes:
        raise ValidationError(
            _(f"{label} size exceeds the maximum limit of {max_size_mb} MB.")
        )

    filename = getattr(file_obj, 'name', '')
    ext = os.path.splitext(filename)[1].lower()

    # 2. Dangerous Extension Check
    if ext in DANGEROUS_EXTENSIONS:
        raise ValidationError(
            _(f"{label} format '{ext}' is not allowed for security reasons.")
        )

    # 3. Allowed Extension Whitelist Check
    if allowed_extensions and ext not in allowed_extensions:
        allowed_str = ", ".join(sorted(allowed_extensions))
        raise ValidationError(
            _(f"Invalid file extension '{ext}'. Allowed formats: {allowed_str}")
        )

    # 4. Content Type / MIME Check
    content_type = getattr(file_obj, 'content_type', '').lower()
    if content_type in DANGEROUS_MIME_TYPES or 'html' in content_type or 'javascript' in content_type:
        raise ValidationError(
            _(f"Unsafe file type detected in {label}.")
        )

    # 5. File Header / Magic Byte Check
    if ext == '.pdf':
        try:
            pos = file_obj.tell()
            header = file_obj.read(5)
            file_obj.seek(pos)
            if not header.startswith(b'%PDF-'):
                raise ValidationError(_("Uploaded file is not a valid PDF document."))
        except Exception:
            pass
    elif ext in ALLOWED_IMAGE_EXTENSIONS:
        try:
            from PIL import Image
            pos = file_obj.tell()
            img = Image.open(file_obj)
            img.verify()
            file_obj.seek(pos)
        except Exception:
            raise ValidationError(_("Uploaded image file appears to be corrupted or invalid."))


def validate_image_file(file_obj):
    """Validator for image uploads (max 5MB)"""
    validate_file_upload(file_obj, allowed_extensions=ALLOWED_IMAGE_EXTENSIONS, max_size_mb=5, label="Image")


def validate_document_file(file_obj):
    """Validator for document & proof uploads (max 10MB)"""
    validate_file_upload(file_obj, allowed_extensions=ALLOWED_DOCUMENT_EXTENSIONS, max_size_mb=10, label="Document")


def validate_video_file(file_obj):
    """Validator for video uploads (max 50MB)"""
    validate_file_upload(file_obj, allowed_extensions=ALLOWED_VIDEO_EXTENSIONS, max_size_mb=50, label="Video")
