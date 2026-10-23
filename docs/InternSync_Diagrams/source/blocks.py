"""Minimal block-diagram helpers (matplotlib). Inches, y grows downward."""
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon, Ellipse, Rectangle

NAVY = "#1F3864"
FILL = "#EAF0FA"
PALE = "#F5F8FC"
AI_FILL = "#FFF4E5"
AI_EDGE = "#C55A11"
EXT_FILL = "#F2F2F2"
EXT_EDGE = "#7F7F7F"
GREEN_FILL = "#E2F0D9"
GREEN_EDGE = "#38761D"
EDGE = "#44546A"
TXT = "#1A1A1A"
plt.rcParams["font.family"] = ["Liberation Sans", "Arial", "DejaVu Sans"]  # first one installed wins

STYLES = {
    "default": (FILL, NAVY, "-"),
    "ai": (AI_FILL, AI_EDGE, "-"),
    "ext": (EXT_FILL, EXT_EDGE, "--"),
    "white": ("white", NAVY, "-"),
    "green": (GREEN_FILL, GREEN_EDGE, "-"),
}


class Canvas:
    def __init__(self, W, H):
        self.W, self.H = W, H
        self.fig = plt.figure(figsize=(W, H))
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set_xlim(0, W)
        self.ax.set_ylim(H, 0)
        self.ax.axis("off")
        self.boxes = {}

    def frame(self, x, y, w, h, title, kind="default", fill=PALE, fs=8.6, align="left", z=0.5):
        _, ec, ls = STYLES[kind]
        fc = fill if kind != "ext" else "white"
        self.ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.10", fc=fc, ec=ec,
                                         lw=1.1, ls=ls, zorder=z))
        tx = x + 0.10 if align == "left" else x + w - 0.10
        self.ax.text(tx, y + 0.08, title, ha=align, va="top", fontsize=fs, fontweight="bold", color=ec,
                     zorder=z + 0.1)

    def box(self, key, x, y, w, h, text, kind="default", fs=7.4, bold_first=False):
        fc, ec, ls = STYLES[kind]
        self.ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.06", fc=fc, ec=ec,
                                         lw=1.0, ls=ls, zorder=2))
        if bold_first and "\n" in text:
            first, rest = text.split("\n", 1)
            n_rest = rest.count("\n") + 1
            lh = fs / 72 * 1.18
            total = lh * (n_rest + 1)
            top = y + h / 2 - total / 2 + lh / 2
            self.ax.text(x + w / 2, top, first, ha="center", va="center", fontsize=fs, fontweight="bold", color=TXT,
                         zorder=3)
            self.ax.text(x + w / 2, top + lh * (n_rest + 1) / 2, rest, ha="center", va="center", fontsize=fs - 0.4,
                         color=TXT, zorder=3, linespacing=1.18)
        else:
            self.ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=TXT, zorder=3,
                         linespacing=1.18)
        self.boxes[key] = (x, y, w, h)

    def cylinder(self, key, x, y, w, h, text, fs=7.4):
        e = 0.12
        self.ax.add_patch(Rectangle((x, y + e / 2), w, h - e, fc=FILL, ec="none", zorder=2))
        self.ax.plot([x, x], [y + e / 2, y + h - e / 2], color=NAVY, lw=1.0, zorder=2.1)
        self.ax.plot([x + w, x + w], [y + e / 2, y + h - e / 2], color=NAVY, lw=1.0, zorder=2.1)
        self.ax.add_patch(Ellipse((x + w / 2, y + h - e / 2), w, e, fc=FILL, ec=NAVY, lw=1.0, zorder=1.9))
        self.ax.add_patch(Ellipse((x + w / 2, y + e / 2), w, e, fc=FILL, ec=NAVY, lw=1.0, zorder=2.2))
        self.ax.text(x + w / 2, y + h / 2 + 0.03, text, ha="center", va="center", fontsize=fs, color=TXT, zorder=3,
                     linespacing=1.18)
        self.boxes[key] = (x, y, w, h)

    # anchors
    def at(self, key, side, f=0.5):
        x, y, w, h = self.boxes[key]
        return {"top": (x + w * f, y), "bottom": (x + w * f, y + h), "left": (x, y + h * f),
                "right": (x + w, y + h * f)}[side]

    def arrow(self, pts, label=None, lpos=None, dashed=False, color=EDGE, both=False, ha="left", fs=6.8, lw=0.95):
        xs, ys = zip(*pts)
        self.ax.plot(xs, ys, color=color, lw=lw, ls=(0, (4, 3)) if dashed else "-", zorder=1.5,
                     solid_joinstyle="miter")
        self._head(pts[-2], pts[-1], color)
        if both:
            self._head(pts[1], pts[0], color)
        if label:
            if lpos is None:
                (x0, y0), (x1, y1) = pts[0], pts[1]
                lpos = ((x0 + x1) / 2 + 0.05, (y0 + y1) / 2)
            self.ax.text(lpos[0], lpos[1], label, fontsize=fs, color="#333333", ha=ha, va="center", zorder=4,
                         linespacing=1.15, bbox=dict(boxstyle="square,pad=0.05", fc="white", ec="none"))

    def _head(self, p0, p1, color):
        ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
        hl, hw = 0.075, 0.035
        bx, by = p1[0] - hl * math.cos(ang), p1[1] - hl * math.sin(ang)
        px, py = -math.sin(ang) * hw, math.cos(ang) * hw
        self.ax.add_patch(Polygon([p1, (bx + px, by + py), (bx - px, by - py)], closed=True, fc=color, ec=color,
                                  lw=0.5, zorder=1.6))

    def text(self, x, y, s, **kw):
        kw.setdefault("fontsize", 7)
        kw.setdefault("color", "#595959")
        self.ax.text(x, y, s, **kw)

    def save(self, path):
        self.fig.savefig(path + ".png", dpi=250)
        self.fig.savefig(path.replace("/png/", "/svg/") + ".svg")
        plt.close(self.fig)
