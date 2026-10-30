"""Requirements status (Increment 5, D2 and RQ-4): every requirement of the SRS with its priority, the increment that
delivered it, its automated tests, and the result recorded in the test reports.

    python docs/tools/trace.py           # writes docs/Requirements_Status.md
    python docs/tools/trace.py --check   # fails if the file is out of date or a requirement is not covered

Sources (Increment 5 design, Section 1): the SRS tables, each increment's 01_Requirements.md, the test code, and each
increment's 04_Test_Report.md. Acceptance test AT-SIM-02 belongs to FR-SIM-02; a test function named
`test_at_sim_02_...` or a file that names `AT-SIM-02` is an automated test of it."""
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
OUT = DOCS / "Requirements_Status.md"
ID = r"(?:FR|NFR)-[A-Z0-9]+-\d+"
SRS_ROW = re.compile(rf"^\| \*\*({ID})\*\* \| (.+?) \| (Must|Should|Could) \|")
SCOPE_ROW = re.compile(rf"^\| ({ID}) \|")
REPORT_ROW = re.compile(rf"^\| ((?:AT-[A-Z0-9]+-\d+)|{ID}) \| (.+) \| ([^|]+) \|\s*$")
TEST_FUNC = re.compile(r"def (test_at_([a-z0-9]+)_(\d+)\w*)")
AT_MENTION = re.compile(r"AT-([A-Z0-9]+)-(\d+)")

# Requirements whose check needs people, devices, or the hosted system; reported as open, not as missing.
KNOWN_OPEN = {
    "NFR-USA-01": "User acceptance testing with 8 participants: plan ready, sessions not yet run (Increment 5, RQ-6)",
    "NFR-REL-01": "Uptime of the demo server during the testing phase: measured on the reference deployment once it "
                  "is switched on; the demonstrations run on the local Docker stack",
    "NFR-SEC-01": "HTTPS only: Vercel and Hugging Face Spaces serve HTTPS only; checked on the reference deployment "
                  "once it is switched on (the local stack is plain HTTP on localhost)",
}


def at_id(req: str) -> str:
    return "AT-" + req.split("-", 1)[1]


def short(text: str, limit: int = 110) -> str:
    text = re.sub(r"\*\*|`", "", text).split(". ")[0].rstrip(".")
    return text if len(text) <= limit else text[:limit - 1].rstrip() + "…"


def srs() -> list[tuple[str, str, str]]:
    rows = []
    for line in (DOCS / "RSR/InternSync_SRS.md").read_text(encoding="utf-8").splitlines():
        m = SRS_ROW.match(line)
        if m:
            rows.append((m.group(1), short(m.group(2)), m.group(3)))
    return rows


def increments() -> dict[str, int]:
    first: dict[str, int] = {}
    for n in range(1, 6):
        path = DOCS / f"Increments/Increment_{n}/01_Requirements.md"
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            m = SCOPE_ROW.match(line)
            if m:
                first.setdefault(m.group(1), n)
    return first


def tests() -> dict[str, set[str]]:
    found: dict[str, set[str]] = defaultdict(set)
    for path in (ROOT / "backend/tests").rglob("*.py"):
        for m in TEST_FUNC.finditer(path.read_text(encoding="utf-8")):
            found[f"AT-{m.group(2).upper()}-{m.group(3)}"].add(m.group(1))
    for folder in ("frontend/src", "frontend/e2e"):
        for path in (ROOT / folder).rglob("*.ts"):
            if path.name.endswith((".test.ts", ".spec.ts")):
                for m in AT_MENTION.finditer(path.read_text(encoding="utf-8")):
                    found[f"AT-{m.group(1)}-{m.group(2)}"].add(f"{path.parent.name}/{path.name}")
    return found


def results() -> dict[str, tuple[int, str]]:
    """The last recorded result of each acceptance test or requirement, with the increment that recorded it."""
    out: dict[str, tuple[int, str]] = {}
    for n in range(1, 6):
        path = DOCS / f"Increments/Increment_{n}/04_Test_Report.md"
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            m = REPORT_ROW.match(line)
            if m:
                out[m.group(1)] = (n, short(m.group(3).strip(), 60))
    return out


def build() -> tuple[str, list[str]]:
    rows, first, found, recorded = srs(), increments(), tests(), results()
    problems, lines, counts = [], [], Counter()
    for req, text, priority in rows:
        auto = sorted(found.get(at_id(req), set()))
        result = recorded.get(at_id(req)) or recorded.get(req)
        if req in KNOWN_OPEN:
            status = "Open"
        elif auto:
            status = "Tested"
        elif result:
            status = "Checked"
        else:
            status = "Not traced"
            if priority in ("Must", "Should"):
                problems.append(f"{req} ({priority}) has neither an automated test nor a recorded check")
        counts[(priority, status)] += 1
        counts[(priority, "all")] += 1
        delivered = f"Increment {first[req]}" if req in first else "—"
        tests_cell = f"{len(auto)}: `{auto[0]}`" + (" …" if len(auto) > 1 else "") if auto else "—"
        recorded_cell = f"{result[1]} (Inc. {result[0]})" if result else "—"
        note = f" {KNOWN_OPEN[req]}" if req in KNOWN_OPEN else ""
        lines.append(f"| {req} | {text} | {priority} | {delivered} | {tests_cell} | {recorded_cell} | "
                     f"**{status}**{note} |")
    srs_ids = {r[0] for r in rows}
    problems += [f"{req} is in an increment's scope but not in the SRS" for req in sorted(set(first) - srs_ids)]

    head = ["| **Priority** | **Requirements** | **Tested (automated, by ID)** | **Checked (result recorded)** | "
            "**Open** | **Not traced** |", "|:---|:--:|:--:|:--:|:--:|:--:|"]
    for priority in ("Must", "Should", "Could"):
        head.append(f"| {priority} | {counts[(priority, 'all')]} | {counts[(priority, 'Tested')]} | "
                    f"{counts[(priority, 'Checked')]} | {counts[(priority, 'Open')]} | "
                    f"{counts[(priority, 'Not traced')]} |")
    total = sum(counts[(p, 'all')] for p in ("Must", "Should", "Could"))
    head.append(f"| **All** | **{total}** | **{sum(counts[(p, 'Tested')] for p in ('Must', 'Should', 'Could'))}** | "
                f"**{sum(counts[(p, 'Checked')] for p in ('Must', 'Should', 'Could'))}** | "
                f"**{sum(counts[(p, 'Open')] for p in ('Must', 'Should', 'Could'))}** | "
                f"**{sum(counts[(p, 'Not traced')] for p in ('Must', 'Should', 'Could'))}** |")
    doc = "\n".join([
        "# InternSync – Requirements Status",
        "",
        "**Generated by `docs/tools/trace.py`; do not edit by hand.** Run `python docs/tools/trace.py` after a change "
        "to the SRS, an increment's scope, the tests, or a test report.",
        "",
        "Each requirement of the [SRS](RSR/InternSync_SRS.md) with the increment that delivered it, its automated "
        "tests (functions named after its acceptance test, for example `test_at_sim_02_…` for FR-SIM-02), and the "
        "last result recorded in the test reports.",
        "",
        "- **Tested:** at least one automated test carries the requirement's acceptance-test ID in its name.",
        "- **Checked:** a result is recorded in a test report. The check may be automated under another test name, "
        "or done in the browser, by a timed run, or by inspection; the test report says which.",
        "- **Open:** the check needs people, devices, or the hosted system and has not been done yet.",
        "",
        "## Summary",
        "",
        *head,
        "",
        "## All Requirements",
        "",
        "| **ID** | **Requirement** | **Priority** | **Delivered in** | **Automated tests** | **Recorded result** | "
        "**Status** |",
        "|:---|:---|:--:|:--:|:---|:---|:---|",
        *lines,
        "",
    ])
    return doc, problems


def main() -> int:
    doc, problems = build()
    if "--check" in sys.argv:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != doc:
            problems.insert(0, "docs/Requirements_Status.md is out of date: run python docs/tools/trace.py")
    else:
        OUT.write_text(doc, encoding="utf-8", newline="\n")
        print(f"wrote {OUT.relative_to(ROOT)}")
    for p in problems:
        print(p)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
