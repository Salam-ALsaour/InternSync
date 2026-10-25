"""Text embeddings for matching (Design 6.2; Increment 2 design, Section 4).

The model runs inside the API process, so no text leaves it (NFR-PRV-02). It is loaded once, on first use. When
`AI_ENABLED` is false, `sentence-transformers` is not installed, or the model cannot be loaded, `get_embedder()`
returns None and every caller uses basic matching (FR-MAT-04)."""
import logging
import re
import threading
from pathlib import Path
from typing import Protocol

from app.core.config import get_settings

log = logging.getLogger("internsync.ai")
DIM = 384
QUERY, PASSAGE = "query: ", "passage: "  # the prefixes the e5 models expect


class Embedder(Protocol):
    version: str

    def encode(self, texts: list[str]) -> list[list[float]]:
        """Unit-length vectors of DIM numbers, one per text."""
        ...


class ModelEmbedder:
    def __init__(self, name: str):
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(name, device="cpu")
        self.model.max_seq_length = 512
        self.version = f"{name}@{_revision(name)}"

    def encode(self, texts: list[str]) -> list[list[float]]:
        vectors = self.model.encode(texts, batch_size=16, normalize_embeddings=True, convert_to_numpy=True,
                                    show_progress_bar=False)
        return [v.astype(float).tolist() for v in vectors]


def _revision(name: str) -> str:
    """The Hugging Face snapshot (commit) of the cached model, read offline; "local" when it cannot be found."""
    try:
        from huggingface_hub import snapshot_download

        path = Path(snapshot_download(name, local_files_only=True))
        if re.fullmatch(r"[0-9a-f]{40}", path.name):
            return path.name[:12]
    except Exception:  # not from the hub, or no cache
        pass
    return "local"


_lock = threading.Lock()
_embedder: Embedder | None = None
_tried = False


def get_embedder() -> Embedder | None:
    global _embedder, _tried
    if _embedder is not None or _tried:
        return _embedder
    with _lock:
        if not _tried:
            _tried = True
            settings = get_settings()
            if settings.ai_enabled:
                try:
                    _embedder = ModelEmbedder(settings.embedding_model)
                    log.info("embedding model loaded: %s", _embedder.version)
                except Exception:  # missing package, no network at build time, broken cache
                    log.exception("embedding model not available; basic matching only")
    return _embedder


def set_embedder(embedder: Embedder | None) -> None:
    """Use this embedder (tests), or none at all (basic mode)."""
    global _embedder, _tried
    with _lock:
        _embedder, _tried = embedder, True
