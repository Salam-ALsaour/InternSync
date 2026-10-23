"""Project charts: schedule (Gantt) and requirements by area and priority."""
import collections
import datetime as dt
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon, Patch, Rectangle

plt.rcParams["font.family"] = ["Liberation Sans", "Arial", "DejaVu Sans"]  # first one installed wins
INK, INK2, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#8a8984", "#e6e5e0", "#ffffff"
S1, S2, S3, GREY = "#2a78d6", "#eb6834", "#1baf7a", "#a3a29c"


def save(fig, name):
    fig.savefig(f"../png/{name}.png", dpi=250, facecolor=SURF)
    fig.savefig(f"../svg/{name}.svg", facecolor=SURF)
    plt.close(fig)


# =================================================================== Gantt
D = lambda m, d: dt.date(2026, m, d)
tasks = [  # id, name, start, end (inclusive), group, depends
    ("T1", "Plan project, collect requirements (SRS)", D(9, 25), D(10, 3), "plan", []),
    ("T2", "System design: architecture, ERD, API", D(10, 4), D(10, 15), "plan", ["T1"]),
    ("T3", "UI/UX design: wireframes", D(10, 4), D(10, 15), "plan", ["T1"]),
    ("T4", "Increment 1: F1, F2, F3, F5, F10", D(10, 16), D(11, 1), "build", ["T2", "T3"]),
    ("T5", "Increment 2: F4, F6–F9 (all Must)", D(11, 2), D(11, 15), "build", ["T4"]),
    ("T6", "Increment 3: F11–F15 (Should)", D(11, 16), D(11, 25), "build", ["T5"]),
    ("T7", "Testing, UAT, fixes (+ Could F16–F19)", D(11, 26), D(12, 10), "test", ["T6"]),
    ("T8", "Final documentation and presentation", D(12, 11), D(12, 15), "test", ["T7"]),
    ("T9", "Project management and monitoring", D(9, 25), D(12, 15), "pm", []),
]
colors = {"plan": S1, "build": S2, "test": S3, "pm": GREY}
names = {"plan": "Planning and design", "build": "Implementation increments", "test": "Testing and delivery",
         "pm": "Project management"}
milestones = [("M1", D(10, 3)), ("M2", D(10, 15)), ("M3", D(11, 1)), ("M4", D(11, 15)), ("M5", D(11, 25)),
              ("M6", D(12, 10)), ("M7", D(12, 15))]

fig = plt.figure(figsize=(7.3, 4.3))
ax = fig.add_axes([0.37, 0.16, 0.6, 0.665])
n = len(tasks)
ypos = {t[0]: n - 1 - i for i, t in enumerate(tasks)}
bh = 0.52
for tid, name, s, e, g, deps in tasks:
    x0 = mdates.date2num(s)
    x1 = mdates.date2num(e + dt.timedelta(days=1))
    y = ypos[tid]
    ax.add_patch(FancyBboxPatch((x0, y - bh / 2), x1 - x0, bh, boxstyle="round,pad=0,rounding_size=0.9",
                                mutation_aspect=0.12, fc=colors[g], ec=SURF, lw=1.0, zorder=3))
# dependency connectors (finish-to-start)
for tid, name, s, e, g, deps in tasks:
    for d in deps:
        src = next(t for t in tasks if t[0] == d)
        xs = mdates.date2num(src[3] + dt.timedelta(days=1))
        ys, yt = ypos[d], ypos[tid]
        xt = mdates.date2num(s)
        ax.plot([xs, xs, xt], [ys - bh / 2, yt, yt], color=MUTED, lw=0.7, zorder=2)
ax.set_ylim(-0.8, n - 0.2 + 0.9)
ax.set_yticks([ypos[t[0]] for t in tasks])
ax.set_yticklabels([f"{t[0]}  {t[1]}" for t in tasks], fontsize=7.4, color=INK)
ax.tick_params(axis="y", length=0, pad=6)
x_lo, x_hi = mdates.date2num(D(9, 22)), mdates.date2num(D(12, 19))
ax.set_xlim(x_lo, x_hi)
ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.SU))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
ax.tick_params(axis="x", labelsize=6.8, colors=INK2, length=0, pad=4)
plt.setp(ax.get_xticklabels(), rotation=0)
for lab in ax.get_xticklabels():
    lab.set_fontsize(6.6)
ax.grid(axis="x", color=GRID, lw=0.6, zorder=0)
for sp in ax.spines.values():
    sp.set_visible(False)
# milestones
ytop = n - 0.2 + 0.45
for m, d in milestones:
    x = mdates.date2num(d + dt.timedelta(days=1))
    ax.plot([x, x], [-0.6, ytop - 0.15], color=INK2, lw=0.6, ls=(0, (2, 2)), zorder=1)
    ax.add_patch(Polygon([(x, ytop - 0.15), (x + 0.9, ytop + 0.05), (x, ytop + 0.25), (x - 0.9, ytop + 0.05)],
                         closed=True, fc=INK, ec=INK, zorder=4))
    ax.text(x, ytop + 0.38, m, ha="center", va="bottom", fontsize=6.8, color=INK, fontweight="bold")
fig.text(0.02, 0.955, "InternSync schedule (SPMP, 2026)", fontsize=10, fontweight="bold", color=INK, va="top")
fig.text(0.02, 0.905, "Bars: activities T1–T9 · diamonds: milestones M1–M7 · grey lines: finish-to-start dependencies",
         fontsize=7, color=INK2, va="top")
handles = [Patch(fc=colors[k], ec="none", label=names[k]) for k in ("plan", "build", "test", "pm")]
fig.legend(handles=handles, loc="lower center", ncol=4, frameon=False, fontsize=7, bbox_to_anchor=(0.55, 0.0),
           handlelength=1.2, handleheight=0.8, columnspacing=1.4)
save(fig, "10_gantt_schedule")

# =================================================================== requirements by area
reqs = json.load(open("reqs.json", encoding="utf-8"))
labels = {
    "FR-AUT": "Accounts and access (FR-AUT)",
    "FR-ORG": "Organizations and verification (FR-ORG)", "FR-CYC": "Cycles and configuration (FR-CYC)",
    "FR-PRF": "Student profile and CV (FR-PRF)", "FR-VAC": "Vacancies and placement (FR-VAC)",
    "FR-MAT": "Matching and explanation (FR-MAT)", "FR-REP": "Weekly and final reports (FR-REP)",
    "FR-ATT": "Attendance (FR-ATT)", "FR-EVL": "Evaluations (FR-EVL)", "FR-WFL": "Approval workflow (FR-WFL)",
    "FR-SIM": "Similarity detection (FR-SIM)", "FR-NOT": "Notifications (FR-NOT)",
    "FR-DSH": "Dashboards and statistics (FR-DSH)", "FR-EXP": "Exports (FR-EXP)",
    "FR-CER": "Certificates (FR-CER)", "FR-LOC": "Language (FR-LOC)", "FR-PWA": "PWA features (FR-PWA)",
    "FR-AUD": "Audit trail (FR-AUD)",
    "NFR-PER": "Performance (NFR-PER)", "NFR-SEC": "Security (NFR-SEC)", "NFR-PRV": "Privacy (NFR-PRV)",
    "NFR-USA": "Usability (NFR-USA)", "NFR-L10N": "Localization (NFR-L10N)",
    "NFR-REL": "Reliability (NFR-REL)", "NFR-MNT": "Maintainability (NFR-MNT)",
    "NFR-PRT": "Portability (NFR-PRT)", "NFR-AI": "AI quality (NFR-AI)",
}
cnt = collections.OrderedDict()
for rid, p in reqs:
    g = rid.rsplit("-", 1)[0]
    cnt.setdefault(g, collections.Counter())[p] += 1
groups = list(cnt.keys())
pcol = {"Must": "#184f95", "Should": "#3987e5", "Could": "#86b6ef"}

fig = plt.figure(figsize=(7.3, 6.8))
ax = fig.add_axes([0.36, 0.09, 0.6, 0.8])
gap_rows = 1.0  # space between FR and NFR blocks
y = 0
ys = {}
for g in groups:
    if g.startswith("NFR") and "NFR" not in ys:
        y += gap_rows
        ys["NFR"] = y
    ys[g] = y
    y += 1
maxy = y
for g in groups:
    yy = maxy - 1 - ys[g]
    left = 0
    for p in ("Must", "Should", "Could"):
        v = cnt[g][p]
        if not v:
            continue
        ax.add_patch(Rectangle((left, yy - 0.34), v, 0.68, fc=pcol[p], ec=SURF, lw=1.2, zorder=3))
        left += v
    ax.text(left + 0.15, yy, str(left), va="center", ha="left", fontsize=7, color=INK2)
ax.set_yticks([maxy - 1 - ys[g] for g in groups])
ax.set_yticklabels([labels[g] for g in groups], fontsize=7.2, color=INK)
ax.tick_params(axis="y", length=0, pad=6)
ax.set_xlim(0, max(sum(c.values()) for c in cnt.values()) + 1.5)
ax.set_ylim(-0.7, maxy - 0.3)
ax.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(1))
ax.tick_params(axis="x", labelsize=6.8, colors=INK2, length=0)
ax.grid(axis="x", color=GRID, lw=0.6, zorder=0)
for sp in ax.spines.values():
    sp.set_visible(False)
ax.set_xlabel("Number of requirements", fontsize=7.4, color=INK2)
# block captions
nfr_top = maxy - 1 - ys["NFR-PER"]
fr_top = maxy - 1 - ys["FR-AUT"]
ax.text(-0.02, fr_top + 0.75, f"FUNCTIONAL ({sum(1 for r, _ in reqs if r.startswith('FR-'))})", transform=ax.get_yaxis_transform(), ha="right", fontsize=7,
        fontweight="bold", color=INK2)
ax.text(-0.02, nfr_top + 0.75, f"NON-FUNCTIONAL ({sum(1 for r, _ in reqs if r.startswith('NFR-'))})", transform=ax.get_yaxis_transform(), ha="right", fontsize=7,
        fontweight="bold", color=INK2)
tot = collections.Counter(p for _, p in reqs)
fig.text(0.02, 0.975, "Requirements by area and priority (SRS v1.2)", fontsize=10, fontweight="bold", color=INK,
         va="top")
fig.text(0.02, 0.945, f"{len(reqs)} requirements: {tot['Must']} Must · {tot['Should']} Should · {tot['Could']} Could"
         " — Must is built in Increments 1–2, Should in Increment 3, Could only if time allows",
         fontsize=7, color=INK2, va="top")
handles = [Patch(fc=pcol[k], ec="none", label=k) for k in ("Must", "Should", "Could")]
fig.legend(handles=handles, loc="upper right", ncol=3, frameon=False, fontsize=7.2, bbox_to_anchor=(0.97, 0.925),
           handlelength=1.2, handleheight=0.8)
save(fig, "11_requirements_priority")
print("ok")
