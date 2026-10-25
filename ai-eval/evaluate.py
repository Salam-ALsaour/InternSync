"""AI evaluation (NFR-AI-03, Design 6.4): skill-extraction recall (FR-PRF-04) and the top-5 hit rate of matching
(FR-MAT-01) on the labelled synthetic set in data/, with the same service code as the API.

    python ai-eval/evaluate.py            # with the embedding model (downloads it once)
    python ai-eval/evaluate.py --basic    # rule-based matching only

Run from the repository root with the backend's Python environment. The set is synthetic (C-09) and labelled by
the author (Increment 2 decision RQ-4)."""
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "backend"))
os.environ.setdefault("ENV", "test")

from app.ai.embeddings import PASSAGE, QUERY, ModelEmbedder  # noqa: E402
from app.ai.skills import find  # noqa: E402
from app.catalog.router import match_terms  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.matching.scoring import Weights, score  # noqa: E402

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
    rows = []
    for i, p in enumerate(profiles):
        eligible = [(j, v) for j, v in enumerate(vacancies) if p["major"] in v["majors"]]
        scored = []
        for j, v in eligible:
            cosine = sum(a * b for a, b in zip(pv[i], vv[j], strict=True)) if embedder is not None else None
            fit = score(p["skills"], v["required"], v["preferred"], cosine, w)
            scored.append((fit.score, fit.required, v["id"]))
        scored.sort(key=lambda x: (-x[0], -x[1]))
        ranked = [vid for _, _, vid in scored]
        top = ranked[:TOP]
        first = next((k for k, vid in enumerate(ranked, start=1) if vid in p["relevant"]), None)
        rows.append({"id": p["id"], "lang": p["lang"], "hit": bool(set(top) & set(p["relevant"])), "top": top,
                     "relevant": p["relevant"], "top1": ranked[:1] != [] and ranked[0] in p["relevant"],
                     "rr": 1 / first if first else 0.0, "pool": len(ranked)})

    def rate(rs, key="hit"):
        return sum(r[key] for r in rs) / len(rs)
    return {"hit_rate": rate(rows), "top1": rate(rows, "top1"), "mrr": rate(rows, "rr"),
            "pool": sum(r["pool"] for r in rows) / len(rows),
            "by_lang": {lang: rate([r for r in rows if r["lang"] == lang]) for lang in ("en", "ar")}, "rows": rows}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--basic", action="store_true", help="rule-based matching only, no model")
    parser.add_argument("--json", action="store_true", help="print the full results as JSON")
    args = parser.parse_args()
    skills, profiles, vacancies = load()
    embedder = None if args.basic else ModelEmbedder(get_settings().embedding_model)
    ext = extraction(skills, profiles)
    mat = matching(profiles, vacancies, embedder)
    if args.json:
        print(json.dumps({"extraction": ext, "matching": mat}, ensure_ascii=False, indent=1))
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
