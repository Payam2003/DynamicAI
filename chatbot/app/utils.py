# funzioni trasversali:
# validazione estensione file, generazione ID unici, gestione dei percorsi, ecc.

import os
import uuid
from pathlib import Path
from fastapi import UploadFile

from app.config import settings


def ensure_upload_dir() -> None:
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)


def get_file_extension(filename: str) -> str:
    return Path(filename).suffix.lower()


def is_allowed_file(filename: str) -> bool:
    return get_file_extension(filename) in settings.ALLOWED_EXTENSIONS


def generate_safe_filename(filename: str) -> str:
    ext = get_file_extension(filename)
    return f"{uuid.uuid4().hex}{ext}"


async def save_upload_file(upload_file: UploadFile) -> dict:
    ensure_upload_dir()

    safe_name = generate_safe_filename(upload_file.filename or "file")
    destination = os.path.join(settings.UPLOAD_DIR, safe_name)

    content = await upload_file.read()

    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise ValueError(
            f"File '{upload_file.filename}' is too large. Max size is {settings.MAX_FILE_SIZE_MB} MB."
        )

    with open(destination, "wb") as f:
        f.write(content)

    return {
        "original_name": upload_file.filename,
        "saved_name": safe_name,
        "path": destination,
        "content_type": upload_file.content_type,
        "size_bytes": len(content),
    }