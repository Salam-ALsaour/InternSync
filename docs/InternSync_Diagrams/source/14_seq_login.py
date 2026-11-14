"""Sequence: sign-in and an authorized request through the pipeline (SDD Section 5.3.1, Design 2.3 and 7.1).
Drawn with matplotlib in the style of the Mermaid sequences 7a–7d."""
import logging
import math
import sys
sys.path.insert(0, ".")
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
from matplotlib.patches import Circle, FancyBboxPatch, Polygon, Rectangle  # noqa: E402
from blocks import Canvas, NAVY, FILL, EDGE, AI_EDGE  # noqa: E402

W, H = 7.3, 8.65
c = Canvas(W, H)
ax = c.ax
LANE = "#8EA9DB"
P = {"U": 0.45, "PWA": 1.75, "API": 3.35, "SVC": 4.95, "DB": 6.6}
NAMES = {"U": "User", "PWA": "React PWA", "API": "FastAPI pipeline\n(core/deps.py)", "SVC": "Auth service /\nmodule service",
         "DB": "PostgreSQL"}
TOP, BOTTOM = 0.12, H - 0.1
n = [0]


def actor(x, y):
    ax.add_patch(Circle((x, y + 0.08), 0.07, fc=FILL, ec=NAVY, lw=0.9, zorder=3))
    ax.plot([x, x], [y + 0.15, y + 0.33], color=NAVY, lw=0.9, zorder=3)
    ax.plot([x - 0.12, x + 0.12], [y + 0.21, y + 0.21], color=NAVY, lw=0.9, zorder=3)
    ax.plot([x, x - 0.1], [y + 0.33, y + 0.45], color=NAVY, lw=0.9, zorder=3)
    ax.plot([x, x + 0.1], [y + 0.33, y + 0.45], color=NAVY, lw=0.9, zorder=3)


for k, x in P.items():
    if k == "U":
        actor(x, TOP)
        ax.text(x, TOP + 0.55, NAMES[k], ha="center", va="center", fontsize=7.2)
    else:
        ax.add_patch(FancyBboxPatch((x - 0.62, TOP), 1.24, 0.5, boxstyle="round,pad=0,rounding_size=0.03", fc=FILL,
                                    ec=NAVY, lw=0.9, zorder=3))
        ax.text(x, TOP + 0.25, NAMES[k], ha="center", va="center", fontsize=7.0, linespacing=1.1, zorder=4)
    ax.plot([x, x], [TOP + 0.62, BOTTOM], color=LANE, lw=1.0, zorder=0.5)


def head(p0, p1, open_=False):
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    hl, hw = 0.08, 0.035
    bx, by = p1[0] - hl * math.cos(ang), p1[1] - hl * math.sin(ang)
    px, py = -math.sin(ang) * hw, math.cos(ang) * hw
    if open_:
        ax.plot([bx + px, p1[0], bx - px], [by + py, p1[1], by - py], color=EDGE, lw=0.9, zorder=2)
    else:
        ax.add_patch(Polygon([p1, (bx + px, by + py), (bx - px, by - py)], closed=True, fc=EDGE, ec=EDGE, zorder=2))


def badge(x, y):
    n[0] += 1
    ax.add_patch(Circle((x, y), 0.075, fc="#44546A", ec="none", zorder=5))
    ax.text(x, y, str(n[0]), ha="center", va="center", fontsize=5.4, color="white", zorder=6, fontweight="bold")


def msg(a, b, y, text, reply=False):
    x0, x1 = P[a], P[b]
    ax.plot([x0, x1 - math.copysign(0.01, x1 - x0)], [y, y], color=EDGE, lw=0.9, ls=(0, (3, 2)) if reply else "-",
            zorder=2)
    head((x0, y), (x1, y), open_=reply)
    badge(x0, y)
    ax.text((x0 + x1) / 2, y - 0.05, text, ha="center", va="bottom", fontsize=6.4, linespacing=1.1, zorder=4,
            bbox=dict(boxstyle="square,pad=0.02", fc="white", ec="none"))


def self_msg(a, y, text, w=0.28):
    x = P[a]
    ax.plot([x, x + w, x + w, x + 0.02], [y, y, y + 0.16, y + 0.16], color=EDGE, lw=0.9, zorder=2)
    head((x + w, y + 0.16), (x, y + 0.16))
    badge(x, y)
    ax.text(x + w + 0.06, y + 0.08, text, ha="left", va="center", fontsize=6.3, linespacing=1.12, zorder=4,
            bbox=dict(boxstyle="square,pad=0.02", fc="white", ec="none"))


def frame(y0, y1, kind, guards, x0=0.2, x1=7.15):
    """guards: list of (y, text); the first is drawn in the header row, later ones as dashed separators."""
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc="none", ec=LANE, lw=0.9, ls=(0, (1.5, 1.5)), zorder=1))
    ax.add_patch(Polygon([(x0, y0), (x0 + 0.38, y0), (x0 + 0.38, y0 + 0.12), (x0 + 0.31, y0 + 0.19), (x0, y0 + 0.19)],
                         closed=True, fc="#EEF3FB", ec=LANE, lw=0.8, zorder=1.2))
    ax.text(x0 + 0.17, y0 + 0.095, kind, ha="center", va="center", fontsize=6.6, color=NAVY, zorder=4)
    for i, (y, t) in enumerate(guards):
        if i:
            ax.plot([x0, x1], [y, y], color=LANE, lw=0.9, ls=(0, (1.5, 1.5)), zorder=1)
        ax.text(x0 + 0.48, y + 0.1, f"[{t}]", ha="left", va="center", fontsize=6.4, color=NAVY, zorder=4,
                bbox=dict(boxstyle="square,pad=0.02", fc="white", ec="none"))


def section(y, text):
    ax.text(0.2, y, text, ha="left", va="center", fontsize=7.2, fontweight="bold", color=NAVY, zorder=4,
            bbox=dict(boxstyle="square,pad=0.03", fc="white", ec="none"))


# ---------------------------------------------------------------- sign-in
y = 1.05
section(y, "Sign-in (FR-AUT-03, NFR-SEC-02, NFR-SEC-03)")
msg("U", "PWA", 1.42, "email and password")
msg("PWA", "API", 1.82, "POST /auth/login")
msg("API", "SVC", 2.2, "login(email, password)")
msg("SVC", "DB", 2.58, "find user by email")
frame(2.75, 5.12, "alt", [(2.75, "locked_until > now"), (3.35, "unknown email or wrong password"), (4.08, "correct password")])
msg("API", "PWA", 3.2, "423 ACCOUNT_LOCKED (even with the right password)", reply=True)
msg("SVC", "DB", 3.67, "failed_logins + 1; on the 5th: locked_until = now + 15 min, audit")
msg("API", "PWA", 3.98, "401 INVALID_CREDENTIALS", reply=True)
self_msg("SVC", 4.2, "verify Argon2id hash; email confirmed,\naccount active", w=0.2)
msg("SVC", "DB", 4.7, "insert user_sessions (sid, expires_at);\nreset failed_logins; audit entry")
msg("API", "PWA", 5.02, "200 {access_token: JWT (sub, role, sid, exp ≤ 12 h), user, idle_timeout_minutes}",
    reply=True)
self_msg("PWA", 5.3, "keep token in memory and sessionStorage;\nstart the 30-minute idle timer", w=0.2)

# ---------------------------------------------------------------- authorized request
section(5.82, "Any later request (Design 2.3; FR-AUT-05, NFR-PRV-01, FR-ORG-02)")
msg("U", "PWA", 6.15, "open a page")
msg("PWA", "API", 6.5, "GET /dashboard  (Authorization: Bearer JWT)")
self_msg("API", 6.66, "verify signature and expiry", w=0.2)
msg("API", "DB", 7.12, "load session by sid: revoked? idle > 30 min?\nupdate last_seen_at (at most once a minute)")
self_msg("API", 7.3, "consent gate → verification gate\n→ role check", w=0.2)
msg("API", "SVC", 7.78, "call the service with the Actor")
msg("SVC", "DB", 8.1, "query filtered by the caller's scope\n(own record, college, or company)")
msg("API", "PWA", 8.45, "200 JSON, or problem+json 401 SESSION_EXPIRED / 403 FORBIDDEN, CONSENT_REQUIRED",
    reply=True)

c.save("../png/14_seq_login")
print("ok")
