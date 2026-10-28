"""AI evaluation (NFR-AI-03, Design 6.4): skill-extraction recall (FR-PRF-04), the top-5 hit rate of matching
(FR-MAT-01), and similarity flags (FR-SIM-02) on the labelled synthetic sets in data/, with the same service code as
the API.

    python ai-eval/evaluate.py            # with the embedding model (downloads it once)
    python ai-eval/evaluate.py --basic    # rule-based matching only

Run from the repository root with the backend's Python environment. The set is synthetic (C-09) and labelled by
the author (Increment 2 decision RQ-4)."""
import argparse
import json
import os
import re
import sys
from math import comb
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "backend"))
os.environ.setdefault("ENV", "test")

from app.ai.embeddings import PASSAGE, QUERY, ModelEmbedder  # noqa: E402
from app.ai.skills import find  # noqa: E402
from app.catalog.router import match_terms  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.matching.scoring import Weights, score  # noqa: E402
from app.similarity.passages import Candidate, overlap, split  # noqa: E402

TOP = 5


def load():
    skills = json.loads((ROOT.parent / "backend/app/seed_data/skills.json").read_text(encoding="utf-8"))
    profiles = json.loads((ROOT / "data/profiles.json").read_text(encoding="utf-8"))
    vacancies = json.loads((ROOT / "data/vacancies.json").read_text(encoding="utf-8"))
    return skills, profiles, vacancies


def extraction(skills, profiles) -> dict:
    index = {}
    for name_en, name_ar, synonyms in sorted(skills):
        for term in match_terms(name_en, name_ar, synonyms):
            index.setdefault(term, name_en)
    rows, hit, total = [], 0, 0
    for p in profiles:
        found = set(find(index, p["cv"]))
        labelled = set(p["skills"])
        hit, total = hit + len(found & labelled), total + len(labelled)
        rows.append({"id": p["id"], "lang": p["lang"], "recall": len(found & labelled) / len(labelled),
                     "missed": sorted(labelled - found), "extra": sorted(found - labelled)})
    by_lang = {lang: sum(len(set(p["skills"]) & set(find(index, p["cv"]))) for p in profiles if p["lang"] == lang)
               / sum(len(p["skills"]) for p in profiles if p["lang"] == lang) for lang in ("en", "ar")}
    return {"recall": hit / total, "by_lang": by_lang, "rows": rows}


def profile_text(p) -> str:
    return QUERY + "\n".join([", ".join(p["skills"]), ", ".join(p["interests"]), p["cv"][:2000]])


def vacancy_text(v) -> str:
    return PASSAGE + "\n".join([v["title"], v["description"], ", ".join(v["required"] + v["preferred"])])


def matching(profiles, vacancies, embedder) -> dict:
    w = Weights()
    if embedder is not None:
        pv = embedder.encode([profile_text(p) for p in profiles])
        vv = embedder.encode([vacancy_text(v) for v in vacancies])
    rows, alone = [], []
    for i, p in enumerate(profiles):
        eligible = [(j, v) for j, v in enumerate(vacancies) if p["major"] in v["majors"]]
        scored, by_text = [], []
        for j, v in eligible:
            cosine = sum(a * b for a, b in zip(pv[i], vv[j], strict=True)) if embedder is not None else None
            fit = score(p["skills"], v["required"], v["preferred"], cosine, w)
            scored.append((fit.score, fit.required, v["id"]))
            by_text.append((cosine or 0.0, 0, v["id"]))
        scored.sort(key=lambda x: (-x[0], -x[1]))
        rows.append(_row(p, [vid for _, _, vid in scored]))
        if embedder is not None:  # the model's own contribution: rank by text similarity only
            by_text.sort(key=lambda x: -x[0])
            alone.append(_row(p, [vid for _, _, vid in by_text]))

    def rate(rs, key="hit"):
        return sum(r[key] for r in rs) / len(rs)

    def summary(rs):
        return {"hit_rate": rate(rs), "top1": rate(rs, "top1"), "mrr": rate(rs, "rr")}
    return {**summary(rows), "pool": sum(r["pool"] for r in rows) / len(rows),
            "by_lang": {lang: rate([r for r in rows if r["lang"] == lang]) for lang in ("en", "ar")}, "rows": rows,
            "text_alone": summary(alone) if alone else None}


def chance(profiles, vacancies) -> dict:
    """What a random order of each profile's eligible vacancies would score, on average: the bar a ranking has to
    clear on this set."""
    hit = top1 = rr = 0.0
    for p in profiles:
        n = sum(1 for v in vacancies if p["major"] in v["majors"])
        r = sum(1 for v in vacancies if p["major"] in v["majors"] and v["id"] in p["relevant"])
        if r == 0:
            continue
        hit += 1 - comb(n - r, TOP) / comb(n, TOP) if n >= TOP else 1.0
        top1 += r / n
        rr += sum(comb(n - k, r - 1) / comb(n, r) / k for k in range(1, n - r + 2))  # first relevant at rank k
    return {"hit_rate": hit / len(profiles), "top1": top1 / len(profiles), "mrr": rr / len(profiles)}


def _row(p, ranked: list[str]) -> dict:
    top = ranked[:TOP]
    first = next((k for k, vid in enumerate(ranked, start=1) if vid in p["relevant"]), None)
    return {"id": p["id"], "lang": p["lang"], "hit": bool(set(top) & set(p["relevant"])), "top": top,
            "relevant": p["relevant"], "top1": ranked[:1] != [] and ranked[0] in p["relevant"],
            "rr": 1 / first if first else 0.0, "pool": len(ranked)}


# ---------------------------------------------------------------- similarity (FR-SIM-02, Increment 3 RQ-6)
SENTENCE = re.compile(r"[^.!?؟]+[.!?؟]")
SIM = {"threshold": 0.30, "cosine": 0.90, "n": 5, "share": 0.5}  # the defaults of Design Table 4.1


def copied_text(item: dict, sources: dict) -> tuple[str, int]:
    """A copied report: its own sentences around the chosen sentences of the source (with light edits)."""
    sentences = [m.group().strip() for m in SENTENCE.finditer(sources[item["source"]]["text"])]
    copied = " ".join(sentences[i] for i in item["sentences"])
    for old, new in item["edits"]:
        copied = copied.replace(old, new)
    text = " ".join(part for part in (item["before"], copied, item["after"]) if part)
    return text, len(copied)


def similarity(embedder) -> dict:
    data = json.loads((ROOT / "data/similarity.json").read_text(encoding="utf-8"))
    sources = {s["id"]: s for s in data["sources"]}
    stored = [(sid, p) for sid, s in sources.items() for p in split(s["text"])]
    vectors = embedder.encode([QUERY + p.text for _, p in stored])
    reports = [{**c, "text": copied_text(c, sources)[0], "copied_share": copied_text(c, sources)[1]
                / len(copied_text(c, sources)[0]), "expected": True} for c in data["copied"]]
    reports += [{**o, "copied_share": 0.0, "expected": False} for o in data["original"]]
    rows = []
    for r in reports:
        parts = split(r["text"])
        mine = embedder.encode([QUERY + part.text for part in parts])
        candidates = []
        for v in mine:
            cosines = sorted(((sum(a * b for a, b in zip(v, w, strict=True)), i) for i, w in enumerate(vectors)),
                             reverse=True)[:5]
            candidates.append([Candidate(stored[i][0], stored[i][1].start, stored[i][1].end, stored[i][1].text, c)
                               for c, i in cosines])
        found = overlap(r["text"], parts, candidates, SIM["cosine"], SIM["n"], SIM["share"])
        best, source = (found[0][0], found[0][1]) if found else (0.0, None)
        rows.append({"id": r["id"], "lang": r["lang"], "expected": r["expected"], "flagged": best >= SIM["threshold"],
                     "score": round(best, 3), "source": source, "copied_share": round(r["copied_share"], 2)})
    copied = [r for r in rows if r["expected"]]
    original = [r for r in rows if not r["expected"]]
    return {"copied_flagged": sum(r["flagged"] for r in copied), "copied": len(copied),
            "original_flagged": sum(r["flagged"] for r in original), "original": len(original),
            "min_copied_share": min(r["copied_share"] for r in copied), "rows": rows}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--basic", action="store_true", help="rule-based matching only, no model")
    parser.add_argument("--json", action="store_true", help="print the full results as JSON")
    args = parser.parse_args()
    skills, profiles, vacancies = load()
    embedder = None if args.basic else ModelEmbedder(get_settings().embedding_model)
    ext = extraction(skills, profiles)
    mat = matching(profiles, vacancies, embedder)
    base = chance(profiles, vacancies)
    sim = similarity(embedder) if embedder is not None else None
    if args.json:
        print(json.dumps({"extraction": ext, "matching": mat, "chance": base, "similarity": sim}, ensure_ascii=False,
                         indent=1))
        return 0
    mode = "basic" if embedder is None else embedder.version
    print(f"Set: {len(profiles)} profiles (10 Arabic, 10 English), {len(vacancies)} vacancies")
    print(f"Skill extraction recall: {ext['recall']:.1%} (English {ext['by_lang']['en']:.1%}, "
          f"Arabic {ext['by_lang']['ar']:.1%}); target 70%")
    for r in ext["rows"]:
        if r["missed"]:
            print(f"  {r['id']} missed: {', '.join(r['missed'])}")
    print(f"Top-{TOP} hit rate ({mode}): {mat['hit_rate']:.1%} (English {mat['by_lang']['en']:.1%}, "
          f"Arabic {mat['by_lang']['ar']:.1%}); target 80%")
    print(f"Top-1 relevant: {mat['top1']:.1%}; mean reciprocal rank: {mat['mrr']:.3f}; "
          f"eligible vacancies per profile: {mat['pool']:.1f} on average")
    for r in mat["rows"]:
        if not r["hit"]:
            print(f"  {r['id']} top {r['top']} relevant {r['relevant']}")
    print(f"A random order would score: top-{TOP} {base['hit_rate']:.1%}, top-1 {base['top1']:.1%}, "
          f"mean reciprocal rank {base['mrr']:.3f}")
    if mat["text_alone"]:
        t = mat["text_alone"]
        print(f"Text similarity alone (no skill rules): top-{TOP} {t['hit_rate']:.1%}, top-1 {t['top1']:.1%}, "
              f"mean reciprocal rank {t['mrr']:.3f}")
    if sim is None:
        print("Similarity: needs the model (run without --basic)")
        return 0
    print(f"Similarity ({len(sim['rows'])} reports; copied ones hold at least {sim['min_copied_share']:.0%} copied text): "
          f"{sim['copied_flagged']} of {sim['copied']} copied flagged (target 9 or more), "
          f"{sim['original_flagged']} of {sim['original']} original flagged (target 1 or fewer)")
    for r in sim["rows"]:
        if r["flagged"] != r["expected"]:
            print(f"  {r['id']} ({r['lang']}) score {r['score']} expected {'flag' if r['expected'] else 'no flag'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
