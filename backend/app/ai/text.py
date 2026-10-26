"""Text extraction from CVs and Arabic/English normalization (Design 6.1). Runs locally (NFR-PRV-02)."""
import io
import re

from docx import Document
from pypdf import PdfReader

from app.core.files import DOCX, PDF

_DIACRITICS = re.compile(r"[ً-ْٰـ]")  # harakat, superscript alef, tatweel
_ARABIC = re.compile(r"[ء-ي]")
_LATIN = re.compile(r"[A-Za-z]")
_TOKENS = re.compile(r"[a-z0-9+#.]+|[ء-ي]+")
MIN_LETTERS = 50


def normalize_text(text: str) -> str:
    s = text.lower()
    s = _DIACRITICS.sub("", s)
    s = s.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ى", "ي").replace("ة", "ه")
    return s


def tokens(text: str) -> list[str]:
    out = []
    for t in _TOKENS.findall(normalize_text(text)):
        t = t.strip(".")
        if t:
            out.append(t)
    return out


def normalize(term: str) -> str:
    """Normal form of a skill name or synonym: tokens joined by single spaces."""
    return " ".join(tokens(term))


def extract_text(data: bytes, mime: str) -> tuple[str, str]:
    """Return (text, status) where status is ok, no_text, or failed (FR-PRF-05)."""
    try:
        if mime == PDF:
            reader = PdfReader(io.BytesIO(data))
            text = "\n".join((page.extract_text() or "") for page in reader.pages)
        elif mime == DOCX:
            doc = Document(io.BytesIO(data))
            parts = [p.text for p in doc.paragraphs]
            for table in doc.tables:
                for row in table.rows:
                    parts.extend(cell.text for cell in row.cells)
            text = "\n".join(parts)
        else:
            return "", "failed"
    except Exception:  # a broken file must not break the upload
        return "", "failed"
    letters = len(_ARABIC.findall(text)) + len(_LATIN.findall(text))
    return text, ("ok" if letters >= MIN_LETTERS else "no_text")


def detect_language(text: str) -> str | None:
    ar, en = len(_ARABIC.findall(text)), len(_LATIN.findall(text))
    total = ar + en
    if total == 0:
        return None
    if ar / total >= 0.7:
        return "ar"
    if en / total >= 0.7:
        return "en"
    return "mixed"
