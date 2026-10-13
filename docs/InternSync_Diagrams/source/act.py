"""Tiny swimlane activity-diagram renderer (matplotlib). Coordinates in inches, y grows downward
internally and is flipped when drawing."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, Polygon, Rectangle

NAVY = "#1F3864"
FILL = "#EAF0FA"
SYS_FILL = "#FFF4E5"
SYS_EDGE = "#C55A11"
EDGE = "#44546A"
LANE_LINE = "#8EA9DB"
TXT = "#1A1A1A"
plt.rcParams["font.family"] = "Liberation Sans"


class Activity:
    def __init__(self, lanes, lane_w=1.5, top=0.55, title=None):
        self.lanes = lanes
        self.lane_w = lane_w
        self.W = lane_w * len(lanes) + 0.2
        self.nodes = {}
        self.edges = []
        self.regions = []
        self.y = top
        self.title = title

    def lx(self, lane):
        return 0.1 + self.lane_w * (self.lanes.index(lane) + 0.5)

    # ---------------------------------------------------------- nodes
    def row(self, gap=0.22):
        self.y += gap

    def action(self, key, lane, text, w=None, system=False, dx=0.0):
        lines = text.count("\n") + 1
        h = 0.16 + 0.13 * lines
        w = w or self.lane_w - 0.22
        x = self.lx(lane) + dx
        self.nodes[key] = dict(kind="action", x=x, y=self.y + h / 2, w=w, h=h, text=text, system=system)
        self.y += h
        return key

    def start(self, key, lane):
        self.nodes[key] = dict(kind="start", x=self.lx(lane), y=self.y + 0.08, w=0.16, h=0.16)
        self.y += 0.16

    def end(self, key, lane):
        self.nodes[key] = dict(kind="end", x=self.lx(lane), y=self.y + 0.1, w=0.2, h=0.2)
        self.y += 0.2

    def connector(self, key, lane, letter):
        self.nodes[key] = dict(kind="connector", x=self.lx(lane), y=self.y + 0.11, w=0.22, h=0.22, text=letter)
        self.y += 0.22

    def decision(self, key, lane, text, dx=0.0, left=False):
        self.nodes[key] = dict(kind="decision", x=self.lx(lane) + dx, y=self.y + 0.16, w=0.32, h=0.32, text=text,
                               left=left)
        self.y += 0.32

    def bar(self, key, lanes):
        xs = [self.lx(l) for l in lanes]
        x0, x1 = min(xs) - 0.45, max(xs) + 0.45
        self.nodes[key] = dict(kind="bar", x=(x0 + x1) / 2, y=self.y + 0.025, w=x1 - x0, h=0.05)
        self.y += 0.05

    def same_row(self, keys_specs):
        """Place several actions on the same row (different lanes)."""
        y0 = self.y
        maxh = 0
        for key, lane, text, system in keys_specs:
            self.y = y0
            self.action(key, lane, text, system=system)
            maxh = max(maxh, self.nodes[key]["h"])
        for key, *_ in keys_specs:  # vertically centre on the tallest
            self.nodes[key]["y"] = y0 + maxh / 2
        self.y = y0 + maxh

    def region(self, k_from, k_to, label):
        self.regions.append((k_from, k_to, label))

    # ---------------------------------------------------------- edges
    def edge(self, a, b, label=None, route=None, label_pos=None, label_ha="left"):
        self.edges.append(dict(a=a, b=b, label=label, route=route, label_pos=label_pos, label_ha=label_ha))

    # ---------------------------------------------------------- drawing
    def draw(self, path, bottom_pad=0.2):
        H = self.y + bottom_pad
        fig = plt.figure(figsize=(self.W, H))
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_xlim(0, self.W)
        ax.set_ylim(H, 0)
        ax.axis("off")
        # lanes
        for i, lane in enumerate(self.lanes):
            x0 = 0.1 + self.lane_w * i
            if lane == "System":
                ax.add_patch(Rectangle((x0, 0.05), self.lane_w, H - 0.1, fc="#FBF7F2", ec="none", zorder=0))
            ax.plot([x0, x0], [0.05, H - 0.05], color=LANE_LINE, lw=0.9, zorder=0)
            ax.text(x0 + self.lane_w / 2, 0.22, lane, ha="center", va="center", fontsize=8.6,
                    fontweight="bold", color=NAVY)
        x_end = 0.1 + self.lane_w * len(self.lanes)
        ax.plot([x_end, x_end], [0.05, H - 0.05], color=LANE_LINE, lw=0.9, zorder=0)
        ax.plot([0.1, x_end], [0.38, 0.38], color=LANE_LINE, lw=0.9, zorder=0)
        ax.plot([0.1, x_end], [0.05, 0.05], color=LANE_LINE, lw=0.9, zorder=0)
        ax.plot([0.1, x_end], [H - 0.05, H - 0.05], color=LANE_LINE, lw=0.9, zorder=0)

        # regions (dashed loop frames)
        for k0, k1, label in self.regions:
            n0, n1 = self.nodes[k0], self.nodes[k1]
            y0 = n0["y"] - n0["h"] / 2 - 0.12
            y1 = n1["y"] + n1["h"] / 2 + 0.10
            ax.add_patch(FancyBboxPatch((0.16, y0), x_end - 0.22, y1 - y0, boxstyle="round,pad=0,rounding_size=0.08",
                                        fc="none", ec="#7F7F7F", lw=0.9, ls=(0, (4, 3)), zorder=1))
            ax.text(0.24, y0 + 0.02, label, ha="left", va="top", fontsize=7.2, color="#595959", style="italic",
                    bbox=dict(boxstyle="square,pad=0.08", fc="white", ec="none"), zorder=2)

        for e in self.edges:
            self._draw_edge(ax, e)
        for key, n in self.nodes.items():
            self._draw_node(ax, n)
        fig.savefig(path + ".png", dpi=250)
        fig.savefig(path.replace("/png/", "/svg/") + ".svg")
        plt.close(fig)

    def _draw_node(self, ax, n):
        k = n["kind"]
        if k == "action":
            fc, ec = (SYS_FILL, SYS_EDGE) if n["system"] else (FILL, NAVY)
            ax.add_patch(FancyBboxPatch((n["x"] - n["w"] / 2, n["y"] - n["h"] / 2), n["w"], n["h"],
                                        boxstyle="round,pad=0,rounding_size=0.07", fc=fc, ec=ec, lw=1.0, zorder=3))
            ax.text(n["x"], n["y"], n["text"], ha="center", va="center", fontsize=7.4, color=TXT, zorder=4,
                    linespacing=1.15)
        elif k == "start":
            ax.add_patch(Circle((n["x"], n["y"]), 0.08, fc=NAVY, ec=NAVY, zorder=3))
        elif k == "end":
            ax.add_patch(Circle((n["x"], n["y"]), 0.1, fc="white", ec=NAVY, lw=1.2, zorder=3))
            ax.add_patch(Circle((n["x"], n["y"]), 0.06, fc=NAVY, ec=NAVY, zorder=4))
        elif k == "decision":
            x, y, r = n["x"], n["y"], 0.16
            ax.add_patch(Polygon([(x, y - r), (x + r, y), (x, y + r), (x - r, y)], closed=True, fc="white",
                                 ec=NAVY, lw=1.0, zorder=3))
            if n.get("left"):
                ax.text(x - r - 0.06, y - 0.03, n["text"], ha="right", va="bottom", fontsize=7.2, color=TXT, zorder=4)
            else:
                ax.text(x + r + 0.06, y - 0.03, n["text"], ha="left", va="bottom", fontsize=7.2, color=TXT, zorder=4)
        elif k == "connector":
            ax.add_patch(Circle((n["x"], n["y"]), 0.11, fc="white", ec=NAVY, lw=1.1, zorder=3))
            ax.text(n["x"], n["y"], n["text"], ha="center", va="center", fontsize=8, fontweight="bold", color=NAVY,
                    zorder=4)
        elif k == "bar":
            ax.add_patch(Rectangle((n["x"] - n["w"] / 2, n["y"] - n["h"] / 2), n["w"], n["h"], fc=NAVY, ec=NAVY,
                                   zorder=3))

    def _anchor(self, n, side, x=None):
        if side == "bottom":
            return (x if x is not None else n["x"], n["y"] + n["h"] / 2)
        if side == "top":
            return (x if x is not None else n["x"], n["y"] - n["h"] / 2)
        if side == "left":
            return (n["x"] - n["w"] / 2, n["y"])
        if side == "right":
            return (n["x"] + n["w"] / 2, n["y"])

    def _arrow(self, ax, pts, label=None, label_pos=None, label_ha="left"):
        xs, ys = zip(*pts)
        ax.plot(xs, ys, color=EDGE, lw=0.95, zorder=2, solid_joinstyle="miter")
        (x0, y0), (x1, y1) = pts[-2], pts[-1]
        import math
        ang = math.atan2(y1 - y0, x1 - x0)
        hl, hw = 0.075, 0.035
        bx, by = x1 - hl * math.cos(ang), y1 - hl * math.sin(ang)
        px, py = -math.sin(ang) * hw, math.cos(ang) * hw
        ax.add_patch(Polygon([(x1, y1), (bx + px, by + py), (bx - px, by - py)], closed=True, fc=EDGE, ec=EDGE,
                             lw=0.5, zorder=2))
        if label:
            lx, ly = label_pos if label_pos else ((pts[0][0] + pts[1][0]) / 2 + 0.05, (pts[0][1] + pts[1][1]) / 2)
            ax.text(lx, ly, label, fontsize=6.8, color="#333333", ha=label_ha, va="center", zorder=5,
                    bbox=dict(boxstyle="square,pad=0.04", fc="white", ec="none"))

    def _draw_edge(self, ax, e):
        a, b = self.nodes[e["a"]], self.nodes[e["b"]]
        r = e["route"]
        if r is None:
            # bottom of a -> top of b; for bars use the other node's x
            xa = b["x"] if a["kind"] == "bar" else a["x"]
            xb = a["x"] if b["kind"] == "bar" else b["x"]
            p0 = (xa, a["y"] + a["h"] / 2)
            p3 = (xb, b["y"] - b["h"] / 2)
            if abs(p0[0] - p3[0]) < 1e-6:
                pts = [p0, p3]
            else:
                ym = p3[1] - 0.10 if b["kind"] != "bar" else p0[1] + 0.10
                if a["kind"] == "bar":
                    ym = p0[1] + 0.001
                    pts = [p0, p3]
                elif b["kind"] == "bar":
                    pts = [p0, (p0[0], p3[1])]
                else:
                    pts = [p0, (p0[0], ym), (p3[0], ym), p3]
            self._arrow(ax, pts, e["label"], e["label_pos"], e["label_ha"])
        else:
            pts = r(a, b)
            self._arrow(ax, pts, e["label"], e["label_pos"], e["label_ha"])
