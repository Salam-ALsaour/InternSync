"""UML use case diagram for InternSync, drawn with matplotlib for precise layout.
Coordinates are in inches on a W x H canvas (y grows upward)."""
import math
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, FancyArrowPatch, Rectangle, Circle

NAVY = "#1F3864"
FILL = "#EAF0FA"
EDGE = "#44546A"
TXT = "#1A1A1A"
AI_FILL = "#FFF4E5"
AI_EDGE = "#C55A11"
plt.rcParams["font.family"] = "Liberation Sans"

W, H = 8.35, 8.8
fig = plt.figure(figsize=(W, H))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, W)
ax.set_ylim(0, H)
ax.axis("off")

EW, EH = 1.62, 0.46  # ellipse size
AW, AH = 1.42, 0.42  # AI sub-use-case size

# ---------------------------------------------------------------- model
actors = {
    "USER": (3.8, 8.30, "User"),
    "ST": (0.60, 6.15, "Student"),
    "CS": (0.27, 3.85, "Company\nSupervisor"),
    "AS": (7.00, 6.15, "Academic\nSupervisor"),
    "CO": (7.45, 4.00, "Coordinator"),
    "PV": (7.00, 1.45, "Public\nVerifier"),
    "SCH": (0.27, 1.05, "Scheduler\n«system»"),
}
cL, cM, cR = 1.93, 3.82, 5.70
cA = 4.02
ucs = {
    "UC02": (cM, 7.35, "UC-02 Activate account,\nlog in, reset password", False),
    "UC03": (cL, 7.05, "UC-03 Build profile and\nconfirm CV skills", False),
    "UC05": (cL, 6.40, "UC-05 View ranked\nvacancies and apply", False),
    "UC07": (cL, 5.75, "UC-07 Submit weekly\nor final report", False),
    "UC14": (cL, 5.10, "UC-14 Evaluate training\nentity, answer survey", False),
    "RANK": (cA, 6.78, "Rank vacancies\n(AI matching)", True),
    "PLAN": (cA, 6.12, "View skill gaps and\ndevelopment plan", True),
    "SIM": (cA, 5.40, "Detect similarity\n(AI)", True),
    "UC08": (cR, 6.60, "UC-08 Review a report\nand check similarity", False),
    "UC11": (cR, 5.25, "UC-11 Enter, submit and\napprove a grade", False),
    "UC01": (cR, 4.62, "UC-01 Open training cycle\nand import users", False),
    "UC04": (cM, 4.25, "UC-04 Submit and\npublish a vacancy", False),
    "UC06": (cM, 3.55, "UC-06 Review applicants\nand confirm placement", False),
    "UC09": (cL, 3.00, "UC-09 Record weekly\nattendance", False),
    "UC10": (cL, 2.35, "UC-10 Submit periodic\nor final evaluation", False),
    "UC12": (cR, 2.60, "UC-12 Export grade\nsheets and summaries", False),
    "UC13": (cR, 1.75, "UC-13 Issue and verify\na certificate", False),
    "UC15": (cL, 1.05, "UC-15 Send reminders,\nlate flags, escalations", False),
}
assoc = [
    ("USER", "UC02"),
    ("ST", "UC03"), ("ST", "UC05"), ("ST", "UC07"), ("ST", "UC14"),
    ("CS", "UC04"), ("CS", "UC06"), ("CS", "UC09"), ("CS", "UC10"),
    ("AS", "UC08"), ("AS", "UC11"),
    ("CO", "UC01"), ("CO", "UC04"), ("CO", "UC06"), ("CO", "UC11"), ("CO", "UC12"), ("CO", "UC13"),
    ("PV", "UC13"),
    ("SCH", "UC15"),
]
rels = [("UC05", "RANK", "«include»"), ("PLAN", "UC05", "«extend»"), ("UC07", "SIM", "«include»")]


# ---------------------------------------------------------------- helpers
def size(key):
    return (AW, AH) if ucs[key][3] else (EW, EH)


def ellipse_point(cx, cy, tx, ty, key=None):
    """Point on the use-case ellipse boundary in the direction of (tx, ty)."""
    w, h = size(key) if key else (EW, EH)
    a, b = w / 2, h / 2
    dx, dy = tx - cx, ty - cy
    k = 1 / math.sqrt((dx / a) ** 2 + (dy / b) ** 2)
    return cx + dx * k, cy + dy * k


def actor_point(ax_, ay_, tx, ty):
    """Attach point beside the actor body, facing the target."""
    side = 1 if tx > ax_ else -1
    return ax_ + 0.16 * side, ay_ + 0.02


def draw_actor(x, y, label, side=False):
    kw = dict(color=NAVY, lw=1.4, solid_capstyle="round", zorder=4)
    ax.add_patch(Circle((x, y + 0.20), 0.065, fill=True, fc="white", ec=NAVY, lw=1.4, zorder=4))
    ax.plot([x, x], [y + 0.135, y - 0.07], **kw)
    ax.plot([x - 0.13, x + 0.13], [y + 0.07, y + 0.07], **kw)
    ax.plot([x, x - 0.11], [y - 0.07, y - 0.25], **kw)
    ax.plot([x, x + 0.11], [y - 0.07, y - 0.25], **kw)
    if side:
        ax.text(x + 0.19, y + 0.02, label, ha="left", va="center", fontsize=8.2, color=TXT, zorder=4)
    else:
        ax.text(x, y - 0.30, label, ha="center", va="top", fontsize=8.2, color=TXT, zorder=4, linespacing=1.1)


# ---------------------------------------------------------------- system boundary
ax.add_patch(Rectangle((1.00, 0.25), 5.60, 7.60, fill=True, fc="white", ec=NAVY, lw=1.6, zorder=0))
ax.text(1.12, 7.72, "InternSync", ha="left", va="top", fontsize=11, fontweight="bold", color=NAVY)

# ---------------------------------------------------------------- generalization bus to "User"
ux, uy = actors["USER"][0], actors["USER"][1]
BUS = uy + 0.0
line = dict(color=EDGE, lw=1.0, zorder=1)
for key in ("ST", "CS"):
    x, y, _ = actors[key]
    ax.plot([x, x], [y + 0.27, BUS], **line)
for key in ("AS", "CO"):
    x, y, _ = actors[key]
    ax.plot([x, x], [y + 0.27, BUS], **line)
for x0, sgn in ((actors["CS"][0], -1), (actors["CO"][0], 1)):
    tip = ux + sgn * 0.19
    start = ux + sgn * 0.36
    ax.plot([x0, start], [BUS, BUS], **line)
    ax.add_patch(FancyArrowPatch((start, BUS), (tip, BUS),
                                 arrowstyle="-|>,head_length=0.55,head_width=0.35", mutation_scale=20,
                                 fc="white", ec=EDGE, lw=1.0, zorder=2, shrinkA=0, shrinkB=0))
ax.text(ux - 1.75, BUS + 0.05, "generalization: every role is a User", fontsize=6.8, color="#595959",
        ha="center", va="bottom", style="italic")

# ---------------------------------------------------------------- associations
for a, u in assoc:
    axx, ayy, _ = actors[a]
    cx, cy, _, _ = ucs[u]
    if a == "USER":
        p0 = (axx, ayy - 0.47)
        p1 = (cx, cy + EH / 2)
    else:
        p0 = actor_point(axx, ayy, cx, cy)
        half = size(u)[0] / 2
        p1 = (cx - half, cy) if axx < cx else (cx + half, cy)
    ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color=EDGE, lw=0.95, zorder=1)

# ---------------------------------------------------------------- include / extend
for s, t, lab in rels:
    sx, sy, _, _ = ucs[s]
    tx, ty, _, _ = ucs[t]
    p0 = ellipse_point(sx, sy, tx, ty, s)
    p1 = ellipse_point(tx, ty, sx, sy, t)
    ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color=AI_EDGE, lw=0.95, linestyle=(0, (4, 3)), zorder=2)
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    for d in (math.radians(155), math.radians(-155)):
        ax.plot([p1[0], p1[0] + 0.10 * math.cos(ang + d)], [p1[1], p1[1] + 0.10 * math.sin(ang + d)],
                color=AI_EDGE, lw=1.0, zorder=2, solid_capstyle="round")
    mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
    ax.text(mx, my + 0.04, lab, fontsize=6.6, color=AI_EDGE, ha="center", va="bottom", zorder=6,
            bbox=dict(boxstyle="square,pad=0.05", fc="white", ec="none"))

# ---------------------------------------------------------------- use cases and actors
for key, (x, y, label, ai) in ucs.items():
    w, h = size(key)
    ax.add_patch(Ellipse((x, y), w, h, fc=AI_FILL if ai else FILL, ec=AI_EDGE if ai else NAVY, lw=1.1, zorder=3))
    ax.text(x, y, label, ha="center", va="center", fontsize=7.6, color=TXT, zorder=4, linespacing=1.15)
for key, (x, y, label) in actors.items():
    draw_actor(x, y, label, side=(key == "CO"))

# legend
ax.add_patch(Ellipse((1.45, 0.52), 0.42, 0.17, fc=AI_FILL, ec=AI_EDGE, lw=1.0, zorder=3))
ax.text(1.72, 0.52, "AI-supported behaviour (advisory)", fontsize=7, va="center", color="#595959")

out = sys.argv[1] if len(sys.argv) > 1 else "../png/01_use_case"
fig.savefig(out + ".png", dpi=250)
fig.savefig(out.replace("/png/", "/svg/") + ".svg")
print("ok")
