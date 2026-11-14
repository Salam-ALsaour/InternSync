"""UML helpers on top of blocks.Canvas: class boxes with three compartments and relations with multiplicities."""
import math

from matplotlib.patches import Polygon, Rectangle

from blocks import NAVY, FILL, AI_EDGE, AI_FILL, TXT, EDGE

KINDS = {"default": (FILL, NAVY), "ai": (AI_FILL, AI_EDGE), "ref": ("#F2F2F2", "#7F7F7F")}


def cls(c, key, x, y, w, name, attrs=(), ops=(), kind="default", fs=5.9, stereo=None):
    """Draw a class box at (x, y) and register it under `key`. Returns the box height."""
    fill, edge = KINDS[kind]
    lh = fs / 72 * 1.32
    head = 0.22 + (0.12 if stereo else 0)
    ha = (len(attrs) * lh + 0.07) if attrs else 0.07
    ho = (len(ops) * lh + 0.07) if ops else 0.07
    h = head + ha + ho
    ls = "--" if kind == "ref" else "-"
    c.ax.add_patch(Rectangle((x, y), w, h, fc="white", ec=edge, lw=0.9, ls=ls, zorder=2))
    c.ax.add_patch(Rectangle((x, y), w, head, fc=fill, ec=edge, lw=0.9, ls=ls, zorder=2.05))
    ty = y + head / 2
    if stereo:
        c.ax.text(x + w / 2, y + 0.09, f"«{stereo}»", ha="center", va="center", fontsize=fs - 0.6, color=edge,
                  zorder=3)
        ty = y + 0.12 + 0.11
    c.ax.text(x + w / 2, ty, name, ha="center", va="center", fontsize=fs + 0.7, fontweight="bold", color=TXT, zorder=3)
    c.ax.plot([x, x + w], [y + head + ha, y + head + ha], color=edge, lw=0.8, ls=ls, zorder=2.1)
    for i, a in enumerate(attrs):
        c.ax.text(x + 0.05, y + head + 0.045 + (i + 0.5) * lh, a, ha="left", va="center", fontsize=fs, color=TXT,
                  zorder=3)
    for i, o in enumerate(ops):
        c.ax.text(x + 0.05, y + head + ha + 0.045 + (i + 0.5) * lh, o, ha="left", va="center", fontsize=fs,
                  color="#1F3864", zorder=3)
    c.boxes[key] = (x, y, w, h)
    return h


def _diamond(c, p0, p1, filled):
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    L, Wd = 0.13, 0.05
    ux, uy = math.cos(ang), math.sin(ang)
    px, py = -uy, ux
    tip = p0
    mid = (p0[0] + ux * L / 2, p0[1] + uy * L / 2)
    back = (p0[0] + ux * L, p0[1] + uy * L)
    pts = [tip, (mid[0] + px * Wd, mid[1] + py * Wd), back, (mid[0] - px * Wd, mid[1] - py * Wd)]
    c.ax.add_patch(Polygon(pts, closed=True, fc=EDGE if filled else "white", ec=EDGE, lw=0.8, zorder=1.7))


def _open_head(c, p0, p1):
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    hl, hw = 0.09, 0.045
    bx, by = p1[0] - hl * math.cos(ang), p1[1] - hl * math.sin(ang)
    px, py = -math.sin(ang) * hw, math.cos(ang) * hw
    c.ax.plot([bx + px, p1[0], bx - px], [by + py, p1[1], by - py], color=EDGE, lw=0.8, zorder=1.7)


def rel(c, pts, kind="assoc", m0=None, m1=None, label=None, lpos=None, m0pos=None, m1pos=None, fs=5.6,
        dashed=False):
    """Relation along `pts` (first point at the source end). kind: assoc, comp (filled diamond at the source),
    agg (hollow diamond at the source), nav (open arrow at the target)."""
    xs, ys = zip(*pts)
    c.ax.plot(xs, ys, color=EDGE, lw=0.8, ls=(0, (3, 2)) if dashed else "-", zorder=1.5)
    if kind in ("comp", "agg"):
        _diamond(c, pts[0], pts[1], kind == "comp")
    if kind == "nav":
        _open_head(c, pts[-2], pts[-1])

    def near(p, q, given, start):
        """Multiplicity next to the end p of the segment p→q: below a horizontal line, right of a vertical one."""
        if given:
            return given[0], given[1], "left"
        dx, dy = q[0] - p[0], q[1] - p[1]
        off = 0.17 if start and kind in ("comp", "agg") else 0.04
        if abs(dx) >= abs(dy):
            return p[0] + math.copysign(off, dx), p[1] + 0.075, "left" if dx > 0 else "right"
        return p[0] + 0.04, p[1] + math.copysign(off + 0.06, dy), "left"

    if m0:
        x, y, ha = near(pts[0], pts[1], m0pos, True)
        c.ax.text(x, y, m0, fontsize=fs, color="#333333", ha=ha, va="center", zorder=4)
    if m1:
        x, y, ha = near(pts[-1], pts[-2], m1pos, False)
        c.ax.text(x, y, m1, fontsize=fs, color="#333333", ha=ha, va="center", zorder=4)
    if label:
        if lpos is None:
            (x0, y0), (x1, y1) = pts[0], pts[1]
            lpos = ((x0 + x1) / 2, (y0 + y1) / 2)
        c.ax.text(lpos[0], lpos[1], label, fontsize=fs, color="#333333", ha="center", va="center", zorder=4,
                  style="italic", bbox=dict(boxstyle="square,pad=0.04", fc="white", ec="none"))
