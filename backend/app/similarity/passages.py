"""Passages and word n-grams for similarity detection (Design 6.3, steps 2 and 4). Pure functions: no database, so
the evaluation script and the unit tests use exactly the code the API uses."""
import re
from collections import defaultdict
from collections.abc import Hashable
from dataclasses import dataclass

from app.ai.text import tokens

MIN_WORDS, MAX_WORDS = 8, 25  # about one sentence: chosen on the evaluation set (CR-09)
_SENTENCE = re.compile(r"[^.!?؟؛\n]+[.!?؟؛]*")
_WORD = re.compile(r"\S+")


@dataclass(frozen=True)
class Passage:
    start: int
    end: int
    text: str


def _sentences(text: str) -> list[tuple[int, int]]:
    out = []
    for m in _SENTENCE.finditer(text):
        start, end = m.start(), m.end()
        while start < end and text[start].isspace():
            start += 1
        while end > start and text[end - 1].isspace():
            end -= 1
        if start < end:
            out.append((start, end))
    return out


def split(text: str) -> list[Passage]:
    """Sentences grouped until a passage holds at least MIN_WORDS words; a sentence longer than MAX_WORDS words is cut
    into pieces of MAX_WORDS words. Each passage keeps its character range in `text`."""
    pieces: list[tuple[int, int, int]] = []  # start, end, words
    for start, end in _sentences(text):
        words = [(m.start() + start, m.end() + start) for m in _WORD.finditer(text[start:end])]
        for i in range(0, len(words), MAX_WORDS):
            chunk = words[i:i + MAX_WORDS]
            pieces.append((chunk[0][0], chunk[-1][1], len(chunk)))
    passages, current = [], None
    for start, end, n in pieces:
        if current is None:
            current = [start, end, n]
        elif current[2] < MIN_WORDS and current[2] + n <= MAX_WORDS:
            current[1], current[2] = end, current[2] + n
        else:
            passages.append(current)
            current = [start, end, n]
    if current is not None:
        if passages and current[2] < MIN_WORDS // 2 and passages[-1][2] + current[2] <= MAX_WORDS:
            passages[-1][1], passages[-1][2] = current[1], passages[-1][2] + current[2]  # a short tail joins
        else:
            passages.append(current)
    return [Passage(s, e, text[s:e]) for s, e, _ in passages]


def ngrams(text: str, n: int) -> set[tuple[str, ...]]:
    words = tokens(text)
    n = min(n, len(words))
    if n == 0:
        return set()
    return {tuple(words[i:i + n]) for i in range(len(words) - n + 1)}


def containment(passage: str, source: str, n: int) -> float:
    """Share of the passage's word n-grams that also appear in the source (normalized Arabic and English words)."""
    mine = ngrams(passage, n)
    if not mine:
        return 0.0
    size = len(next(iter(mine)))
    return len(mine & ngrams(source, size)) / len(mine)


@dataclass(frozen=True)
class Candidate:
    """A stored passage found near a passage of the checked report."""
    source: Hashable  # the source report version
    start: int
    end: int
    text: str
    cosine: float


def overlap(body: str, parts: list[Passage], candidates: list[list[Candidate]], cos_min: float, n: int,
            share: float, top: int = 5) -> list[tuple[float, Hashable, list[dict]]]:
    """Design 6.3, steps 4 and 5, as changed by CR-09: a passage counts for a source report when one of that
    report's passages near it reaches `cos_min` and at least `share` of the passage's word n-grams appear in that
    report's passages near it, taken together. Passages of two reports seldom line up, so a copied passage often
    spans two source passages. Per source: characters of the report covered by counted passages ÷ characters of the
    report. Returns the `top` sources, best first, with their passage pairs."""
    ranges: dict[Hashable, list[tuple[int, int]]] = defaultdict(list)
    pairs: dict[Hashable, list[dict]] = defaultdict(list)
    for passage, found in zip(parts, candidates, strict=True):
        by_source: dict[Hashable, list[Candidate]] = defaultdict(list)
        for c in found:
            by_source[c.source].append(c)
        for source, near in by_source.items():
            if max(c.cosine for c in near) < cos_min:
                continue
            near.sort(key=lambda c: c.start)
            if containment(passage.text, " ".join(c.text for c in near), n) >= share:
                ranges[source].append((passage.start, passage.end))
                shown = [c for c in near if containment(passage.text, c.text, n) > 0]  # only passages with shared words
                pairs[source] += [{"report": [passage.start, passage.end], "source": [c.start, c.end],
                                   "cosine": round(float(c.cosine), 4)} for c in shown]
    length = max(len(body), 1)
    scores = sorted(((covered(r) / length, source) for source, r in ranges.items()), key=lambda x: -x[0])[:top]
    return [(min(score, 1.0), source, pairs[source]) for score, source in scores]


def covered(ranges: list[tuple[int, int]]) -> int:
    """Characters covered by possibly overlapping ranges."""
    total, last = 0, -1
    for start, end in sorted(ranges):
        start = max(start, last)
        if end > start:
            total += end - start
            last = end
    return total
