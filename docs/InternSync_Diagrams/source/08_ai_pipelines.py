"""AI pipelines: matching (F4/F11) and similarity detection (F12) — proposed design."""
import sys
sys.path.insert(0, ".")
from blocks import Canvas, AI_EDGE, NAVY

W, H = 7.3, 6.55
c = Canvas(W, H)

# ======================================================= matching
c.frame(0.12, 0.12, 7.06, 3.62, "A. Matching and explanation (F4, F11)", kind="ai", fill="#FFFBF5", fs=8.6)
bw, bh, y1 = 1.55, 0.62, 0.55
c.box("cv", 0.3, y1, bw, bh, "CV upload\n(PDF / DOCX)", kind="white")
c.box("ext", 2.05, y1, bw, bh, "Text extraction\n+ skill extraction\n(vocabulary, synonyms)", kind="ai")
c.box("conf", 3.8, y1, bw, bh, "Student confirms\nor edits skills\n(human check)")
c.box("emb", 5.55, y1, bw, bh, "Embed profile text\nmultilingual-e5-small\n(384-d, AR + EN)", kind="ai")
for a, b in (("cv", "ext"), ("ext", "conf"), ("conf", "emb")):
    c.arrow([c.at(a, "right"), c.at(b, "left")], color=AI_EDGE)

y2 = 1.62
c.box("vac", 0.3, y2, bw, bh, "Published vacancies\n(embedded when\npublished)", kind="white")
c.box("elig", 2.05, y2, bw, bh, "Eligibility filter\ncycle, open, university,\nmajor, min GPA\n(FR-MAT-03)")
c.box("score", 3.8, y2, 3.3, bh, "", kind="ai")
c.ax.text(3.8 + 1.65, y2 + 0.17, "fit = 100 × (0.5·semantic + 0.4·required + 0.1·preferred)", ha="center",
          va="center", fontsize=7.4, fontweight="bold", color="#1A1A1A", zorder=3)
c.ax.text(3.8 + 1.65, y2 + 0.43, "semantic = cosine(profile, vacancy)   required / preferred =\n"
          "share of the vacancy's required / preferred skills the student has", ha="center", va="center",
          fontsize=6.6, color="#333333", zorder=3, linespacing=1.2)
c.arrow([c.at("vac", "right"), c.at("elig", "left")], color=AI_EDGE)
c.arrow([c.at("elig", "right"), c.at("score", "left")], color=AI_EDGE)
c.arrow([c.at("emb", "bottom"), (c.at("emb", "bottom")[0], y2)], color=AI_EDGE)

y3 = 2.62
c.box("rank", 0.3, y3, bw, bh, "Ranked list\n(descending fit,\nlabelled advisory)", kind="green")
c.box("expl", 2.05, y3, bw, bh, "Explanation:\nmatched and missing\nrequired skills")
c.box("plan", 3.8, y3, bw, bh, "Development plan:\nlearning resources\nper missing skill")
c.box("fb", 5.55, y3, bw, bh, "Fallback (FR-MAT-04):\nmodel unavailable →\nrules only, \"Basic\"", kind="white")
sc = c.at("score", "bottom", 0.3)
c.arrow([sc, (sc[0], 2.45), (c.at("rank", "top")[0], 2.45), c.at("rank", "top")], color=AI_EDGE)
c.arrow([c.at("rank", "right"), c.at("expl", "left")], color=AI_EDGE)
c.arrow([c.at("expl", "right"), c.at("plan", "left")], color=AI_EDGE)
c.arrow([c.at("fb", "top"), c.at("score", "bottom", 0.78)], dashed=True, color=AI_EDGE)
c.text(0.3, 3.42, "Weights are a proposed starting point, stored as configuration and tuned on the labelled set "
       "(target: a relevant vacancy in the top 5 for ≥ 80 % of 20 profiles, O2).", fontsize=6.6, va="center",
       color="#595959")

# ======================================================= similarity
c.frame(0.12, 3.92, 7.06, 2.5, "B. Similarity detection (F12) — runs after each submission", kind="ai",
        fill="#FFFBF5", fs=8.6)
y4 = 4.35
c.box("sub", 0.3, y4, 1.2, bh, "Report\nsubmitted", kind="white")
c.box("chunk", 1.68, y4, 1.2, bh, "Split into\npassages\n(~2–3 sentences)", kind="ai")
c.box("emb2", 3.06, y4, 1.2, bh, "Embed each\npassage", kind="ai")
c.box("knn", 4.44, y4, 1.2, bh, "Nearest passages,\nsame university\n(pgvector)", kind="ai")
c.box("conf2", 5.82, y4, 1.28, bh, "Confirm overlap:\ncosine ≥ 0.90 and\nword 5-gram match", kind="ai")
for a, b in (("sub", "chunk"), ("chunk", "emb2"), ("emb2", "knn"), ("knn", "conf2")):
    c.arrow([c.at(a, "right"), c.at(b, "left")], color=AI_EDGE)

y5 = 5.35
c.box("pct", 3.06, y5, 2.58, bh, "score = overlapping characters ÷ report\ncharacters, per source report", kind="ai")
c.box("flag", 5.82, y5, 1.28, bh, "≥ 30 % (default):\nflag + passages\nside by side", kind="green")
c.box("human", 0.3, y5, 2.58, bh, "Academic supervisor decides: No issue /\nOverlap confirmed (advisory, FR-SIM-03)")
cf = c.at("conf2", "bottom", 0.3)
c.arrow([cf, (cf[0], 5.2), (c.at("pct", "top", 0.5)[0], 5.2), c.at("pct", "top", 0.5)], color=AI_EDGE)
c.arrow([c.at("pct", "right"), c.at("flag", "left")], color=AI_EDGE)
fl = c.at("flag", "bottom")
c.arrow([fl, (fl[0], 6.12), (c.at("human", "bottom")[0], 6.12), c.at("human", "bottom")], color=NAVY)
c.text(3.0, 6.25, "Excludes the student's own earlier versions; compares all cycles of the same university only (FR-SIM-01).",
       fontsize=6.6, va="center", ha="center", color="#595959")

c.save("../png/08_ai_pipelines")
print("ok")
