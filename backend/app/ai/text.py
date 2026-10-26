"""Text extraction from CVs and Arabic/English normalization (Design 6.1). Runs locally (NFR-PRV-02)."""
import io
import re
import zipfile

from docx import Document
from pypdf import PdfReader
from pypdf.generic import DecodedStreamObject

from app.core.files import DOCX, PDF

_DIACRITICS = re.compile(r"[ً-ْٰـ]")  # harakat, superscript alef, tatweel
_ARABIC = re.compile(r"[ء-ي]")
_LATIN = re.compile(r"[A-Za-z]")
_TOKENS = re.compile(r"[a-z0-9+#.]+|[ء-ي]+")
MIN_LETTERS = 50
# Bounds on the work for one file (NFR-PER-03): a CV page holds a few kilobytes of drawing instructions, but a crafted
# or compressed file can hold megabytes, and reading text from one page slows down faster than its size grows.
MAX_PAGES = 20
MAX_PAGE_CONTENT = 512 * 1024  # bytes of one page's instructions that are read for text
MAX_PDF_CONTENT = 2 * 1024 * 1024  # bytes of instructions read from the whole file
MAX_DOCX_UNPACKED = 50 * 1024 * 1024  # bytes of a DOCX once unzipped


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
            text = _pdf_text(data)
        elif mime == DOCX:
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                if sum(i.file_size for i in z.infolist()) > MAX_DOCX_UNPACKED:
                    return "", "failed"
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


def _pdf_text(data: bytes) -> str:
    """Text of the first MAX_PAGES pages. A page with more instructions than MAX_PAGE_CONTENT is cut after the last
    complete text object within the limit, and reading stops once MAX_PDF_CONTENT has been read."""
    parts, budget = [], MAX_PDF_CONTENT
    for page in PdfReader(io.BytesIO(data)).pages[:MAX_PAGES]:
        contents = page.get_contents()
        if contents is None:
            continue
        raw = contents.get_data()
        limit = min(MAX_PAGE_CONTENT, budget)
        if len(raw) > limit:
            end = raw.rfind(b"ET", 0, limit)
            short = DecodedStreamObject()
            short.set_data(raw[:end + 2] if end >= 0 else b"")
            page.replace_contents(short)
        parts.append(page.extract_text() or "")
        budget -= min(len(raw), limit)
        if budget <= 0:
            break
    return "\n".join(parts)


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
