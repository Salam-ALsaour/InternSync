"""Write the table of Appendix 11.2 of the STS from the increment documents: each acceptance test of Section 6 of
Increment_N/01_Requirements.md with its latest result from Section 3 of Increment_N/04_Test_Report.md. A test
specified in two increments (AT-AI-03, AT-PWA-03) keeps its latest scenario and result.

    python docs/Project_7_STS/build/acceptance_table.py           # from the repository root, or with --check in CI"""
import re
import sys
from pathlib import Path

DOCS = Path(__file__).resolve().parents[2]
STS = DOCS / "Project_7_STS" / "InternSync_STS.md"
START, END = "<!-- acceptance-table -->", "<!-- /acceptance-table -->"


def rows(text, heading):
    """Rows of the first pipe table under `heading` whose first cell is an acceptance test ID."""
    part = text.split(heading, 1)[1] if heading in text else ""
    out = []
    for line in part.splitlines()[1:]:
        if line.startswith("## "):
            break
        cells = [c.strip() for c in re.split(r"(?<!\\)\|", line.strip())[1:-1]]
        if cells and re.fullmatch(r"\**AT-[A-Z0-9]+-\d+\**", cells[0]):
            out.append([cells[0].strip("*")] + cells[1:])
    return out


def table():
    spec, result = {}, {}
    for n in range(1, 6):
        folder = DOCS / "Increments" / f"Increment_{n}"
        for r in rows((folder / "01_Requirements.md").read_text(encoding="utf-8"), "## 6. Acceptance Tests"):
            spec[r[0]] = r[1:4]
        for r in rows((folder / "04_Test_Report.md").read_text(encoding="utf-8"), "## 3. Acceptance Tests"):
            result[r[0]] = r[-1]
    missing = sorted(set(spec) - set(result))
    if missing:
        raise SystemExit(f"no result for {', '.join(missing)}")
    lines = [f"**Table 11.1 – The {len(spec)} acceptance tests and their latest results**", "",
             "| **Test** | **Requirement** | **Scenario and expected result** | **Level** | **Result** |",
             "|:---|:---|:---|:---|:---|"]
    lines += [f"| {k} | {req} | {scenario} | {level} | {result[k]} |" for k, (req, scenario, level) in spec.items()]
    return "\n".join(lines)


def main():
    text = STS.read_text(encoding="utf-8")
    if START not in text:
        raise SystemExit(f"{START} not found in {STS.name}")
    head, rest = text.split(START, 1)
    tail = rest.split(END, 1)[1] if END in rest else rest
    new = f"{head}{START}\n\n{table()}\n\n{END}{tail}"
    if "--check" in sys.argv:
        if new != text:
            raise SystemExit("Appendix 11.2 of the STS is out of date: run docs/Project_7_STS/build/acceptance_table.py")
        print("Appendix 11.2 is up to date")
        return
    STS.write_text(new, encoding="utf-8")
    print(f"wrote {len(table().splitlines()) - 4} rows into {STS.relative_to(DOCS.parent)}")


if __name__ == "__main__":
    main()
