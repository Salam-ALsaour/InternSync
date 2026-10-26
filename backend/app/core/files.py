"""File storage and upload checks (NFR-SEC-04, Design 5.5). Types are detected from the content, never
from the file name; files live outside any web root under random keys."""
import hashlib
import io
import uuid
import zipfile
from functools import lru_cache
from pathlib import Path

import filetype
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core import clock
from app.core.config import get_settings
from app.core.errors import ApiError
from app.models import StoredFile, User

PDF, DOCX, PNG, JPEG = ("application/pdf",
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        "image/png", "image/jpeg")
DOCUMENTS = {PDF, DOCX}
DOCUMENTS_AND_IMAGES = {PDF, DOCX, PNG, JPEG}
VERIFICATION_TYPES = {PDF, PNG, JPEG}


def detect_type(data: bytes) -> str | None:
    if data.startswith(b"%PDF-"):
        return PDF
    kind = filetype.guess(data[:8192])
    if kind and kind.mime in (PNG, JPEG):
        return kind.mime
    if data.startswith(b"PK"):
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                names = set(z.namelist())
            if "[Content_Types].xml" in names and "word/document.xml" in names:
                return DOCX
        except zipfile.BadZipFile:
            return None
    return None


def read_upload(upload: UploadFile, max_mb: int) -> bytes:
    limit = max_mb * 1024 * 1024
    data = upload.file.read(limit + 1)
    if len(data) > limit:
        raise ApiError(413, "FILE_TOO_LARGE", max_mb=max_mb)
    return data


class LocalStorage:
    def __init__(self, base: str):
        self.base = Path(base).resolve()

    def _path(self, key: str) -> Path:
        path = (self.base / key).resolve()
        if self.base not in path.parents:
            raise ValueError("storage key escapes the storage directory")
        return path

    def save(self, key: str, data: bytes) -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def read(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def exists(self, key: str) -> bool:
        return self._path(key).exists()

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)

    def prepare(self) -> None:
        self.base.mkdir(parents=True, exist_ok=True)


@lru_cache
def _supabase():
    from app.core.storage_supabase import SupabaseStorage

    s = get_settings()
    return SupabaseStorage(s.supabase_url, s.supabase_service_key, s.storage_bucket)


def storage():
    """`local` (a directory, for development and the local demo) or `supabase` (the reference deployment)."""
    settings = get_settings()
    if settings.storage_backend == "supabase":
        return _supabase()
    return LocalStorage(settings.local_storage_dir)


def store(db: Session, data: bytes, original_name: str, purpose: str, allowed: set[str],
          uploader: User | None) -> StoredFile:
    mime = detect_type(data)
    if mime is None or mime not in allowed:
        raise ApiError(415, "UNSUPPORTED_FILE_TYPE")
    prefix = "verification" if purpose == "verification_document" else purpose
    key = f"{prefix}/{clock.now():%Y}/{uuid.uuid4()}"
    storage().save(key, data)
    row = StoredFile(storage_key=key, original_name=(original_name or "file")[:200], mime_type=mime,
                     size_bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), purpose=purpose,
                     uploaded_by=uploader.id if uploader else None)
    db.add(row)
    db.flush()
    return row
