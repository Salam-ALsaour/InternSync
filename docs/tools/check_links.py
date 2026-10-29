"""Every relative link and image in the maintained Markdown documents points to a file that exists (Increment 5,
check C-1). Web links and anchors inside a page are not checked.

    python docs/tools/check_links.py"""
import re
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)|<img[^>]+src=\"([^\"]+)\"")
SKIP = ("http://", "https://", "mailto:", "#")


def documents() -> list[Path]:
    docs = [p for p in (ROOT / "docs").rglob("*.md") if "old" not in p.parts]
    return [ROOT / "README.md", *sorted(docs)]


def main() -> int:
    broken = []
    for doc in documents():
        text = re.sub(r"```.*?```", "", doc.read_text(encoding="utf-8"), flags=re.S)  # no links inside code
        for m in LINK.finditer(text):
            target = m.group(1) or m.group(2)
            if target.startswith(SKIP) or target.startswith("<"):
                continue
            path = unquote(target.split("#", 1)[0])
            if path and not (doc.parent / path).exists():
                broken.append(f"{doc.relative_to(ROOT)}: {target}")
    print("\n".join(broken) or f"{len(documents())} documents, no broken link")
    return 1 if broken else 0


if __name__ == "__main__":
    raise SystemExit(main())
