"""Permission matrix (AT-AUT-05, Increment 1 design, Section 11): every route × every caller that the matrix
does not allow gets 401 (no sign-in) or 403, and every registered route is in the matrix."""
import re
import uuid
from pathlib import Path

import yaml
from fastapi.routing import APIRoute

from app.main import app

MATRIX = yaml.safe_load((Path(__file__).parent / "matrix.yaml").read_text(encoding="utf-8"))
CALLERS = ("public", "unverified", "st", "cs", "ca", "as", "co", "pa")


def registered_routes() -> set[str]:
    out = set()
    for included in app.router.routes:
        if type(included).__name__ != "_IncludedRouter":
            continue
        for r in included.original_router.routes:
            if isinstance(r, APIRoute):
                out |= {f"{m} /api/v1{r.path}" for m in r.methods}
    return out


def fill(path: str) -> str:
    def value(m: re.Match) -> str:
        name = m.group(1)
        if name == "week_no":
            return "1"
        if name == "token":
            return "x" * 43
        return str(uuid.uuid4())
    return re.sub(r"\{(\w+)\}", value, path)


def test_every_route_is_in_the_matrix_and_nothing_else():
    routes = registered_routes()
    assert routes - set(MATRIX) == set(), "routes missing from matrix.yaml"
    assert set(MATRIX) - routes == set(), "matrix.yaml lists routes that do not exist"
    for key, allowed in MATRIX.items():
        assert set(allowed) <= set(CALLERS), key


def test_at_aut_05_disallowed_callers_are_refused(client, w, f, db):
    pending = f.student(w.A1, w.cs_major, status="pending")
    db.commit()
    headers = {"public": {}, "unverified": f.headers(pending), "st": f.headers(w.stA), "cs": f.headers(w.cs1),
               "ca": f.headers(w.ca1), "as": f.headers(w.asA1), "co": f.headers(w.coA1), "pa": f.headers(w.pa)}
    failures, calls = [], 0
    for key, allowed in MATRIX.items():
        if "public" in allowed:
            continue
        method, path = key.split(" ", 1)
        for caller in CALLERS:
            if caller in allowed:
                continue
            calls += 1
            r = client.request(method, fill(path), headers=headers[caller], json={})
            expected = 401 if caller == "public" else 403
            if r.status_code != expected:
                failures.append(f"{key} as {caller}: {r.status_code} {r.text[:120]}")
    assert calls > 300
    assert failures == []


def test_allowed_callers_pass_the_role_gates(client, w, f):
    """A smoke check in the other direction: allowed callers never get the role-gate 403 on list routes."""
    for key, caller, h in (("GET /api/v1/cycles", "st", f.headers(w.stA)),
                           ("GET /api/v1/users", "ca", f.headers(w.ca1)),
                           ("GET /api/v1/audit-log", "pa", f.headers(w.pa)),
                           ("GET /api/v1/placements", "as", f.headers(w.asA1))):
        assert caller in MATRIX[key]
        assert client.get(key.split(" ", 1)[1], headers=h).status_code == 200, key
