"""Swimlane activity diagrams of the co-op life cycle (two parts)."""
import sys
sys.path.insert(0, ".")
from act import Activity

L = ["Student", "Company Supervisor", "Academic Supervisor", "Coordinator", "System"]
ST, CS, AS, CO, SY = L
PA = "Platform Admin"

# ------------------------------------------------------------------ Part 1
L1 = [ST, CS, AS, CO, PA, SY]
a = Activity(L1, lane_w=1.4, top=0.55)
a.start("s", PA); a.row(0.2)
a.action("o1", PA, "Add university\nand its colleges"); a.row()
a.bar("f0", [CS, CO, PA]); a.row()
a.same_row([("k1", CS, "Company Admin\nregisters (proof:\ncommercial reg.)", False),
            ("c0", CO, "Coordinator\nregisters (proof:\nappointment letter)", False)])
a.row()
a.bar("j0", [CS, CO, PA]); a.row()
a.action("a1", PA, "Verify coordinator\nand company\n(check proof)"); a.row()
a.bar("f1", [CS, CO, PA]); a.row()
a.same_row([("v1", CS, "Invite company\nsupervisors; publish\nvacancies (no review)", False),
            ("c1", CO, "Open training cycle;\ninvite academic\nsupervisors", False)])
a.row()
a.bar("j1", [ST, CS, CO]); a.row()
a.action("r1", ST, "Register with\nenrolment proof"); a.row()
a.action("r2", CO, "Verify student;\nenrol in cycle"); a.row(0.16)
a.decision("d1", CO, "Verified?"); a.row(0.2)
a.action("p1", ST, "Upload CV\n(PDF / DOCX)"); a.row()
a.action("p2", SY, "Extract skills from\nCV text (AR / EN)", system=True); a.row()
a.action("p3", ST, "Confirm or edit\nextracted skills"); a.row()
a.action("p4", SY, "Rank eligible\nvacancies: fit score,\nmatched and\nmissing skills", system=True); a.row()
a.action("p5", ST, "Apply\n(max 5 active)"); a.row()
a.action("p6", CS, "Accept or decline\napplicants"); a.row()
a.action("p7", CO, "Confirm placement;\nassign academic\nsupervisor"); a.row()
a.action("p8", SY, "Create weekly and\nfinal report slots", system=True); a.row(0.2)
a.connector("A", SY, "A")

for x, y in [("s", "o1"), ("o1", "f0"), ("f0", "k1"), ("f0", "c0"), ("k1", "j0"), ("c0", "j0"), ("j0", "a1"),
             ("a1", "f1"), ("f1", "v1"), ("f1", "c1"), ("v1", "j1"), ("c1", "j1"), ("j1", "r1"), ("r1", "r2"),
             ("r2", "d1"), ("p1", "p2"), ("p2", "p3"), ("p3", "p4"), ("p4", "p5"), ("p5", "p6"), ("p6", "p7"),
             ("p7", "p8"), ("p8", "A")]:
    a.edge(x, y)
a.edge("d1", "p1", "yes", label_pos=None)


def back_to_r1(d, r):
    xr = r["x"] + r["w"] / 2
    xc = xr + 0.28
    return [(d["x"] - 0.16, d["y"]), (xc, d["y"]), (xc, r["y"]), (xr, r["y"])]


_r, _d = a.nodes["r1"], a.nodes["d1"]
a.edge("d1", "r1", "no: rejected\nwith reason", route=back_to_r1,
       label_pos=(_r["x"] + _r["w"] / 2 + 0.33, (_r["y"] + _d["y"]) / 2))
a.draw("../png/03a_activity_setup_placement")


# ------------------------------------------------------------------ Part 2
b = Activity(L, top=0.55)
b.connector("A", SY, "A"); b.row(0.18)
b.bar("f1", L); b.row(0.2)
b.same_row([("w1", ST, "Submit weekly\nreport (save\ndraft, submit)", False),
            ("w2", CS, "Record weekly\nattendance (+ periodic\nevaluation at mid-point)", False),
            ("w3", SY, "Remind 24 h before\ndeadline if not\nsubmitted", True)])
b.row()
b.action("w4", SY, "Stamp server time,\nflag Late / Missing,\ncheck similarity", system=True); b.row()
b.action("w5", AS, "Accept report or\nrequest revision"); b.row()
b.bar("j1", L); b.row(0.30)
b.decision("d2", SY, "More training\nweeks?", left=True); b.row(0.24)
b.bar("f2", L); b.row(0.2)
b.same_row([("e1", ST, "Submit final report", False),
            ("e2", CS, "Submit final\nevaluation (rubric)", False)])
b.row()
b.action("e3", AS, "Accept final report"); b.row()
b.bar("j2", L); b.row(0.2)
b.action("g1", AS, "Enter component\nscores; submit grade"); b.row()
b.action("g2", CO, "Review grade", w=1.12, dx=0.13); b.row(0.16)
b.decision("d3", CO, "Approved?", dx=0.13); b.row(0.2)
b.action("g3", CO, "Grade becomes\nFinal (locked);\nvisible to student", w=1.12, dx=0.13); b.row()
b.action("g4", CO, "Export grade\nsheets; issue\ncertificates", w=1.12, dx=0.13); b.row()
b.action("g5", ST, "Evaluate training\nentity; answer\noutcome survey"); b.row(0.2)
b.end("e", ST)
b.region("f1", "j1", "loop: each training week")

for x, y in [("A", "f1"), ("f1", "w1"), ("f1", "w2"), ("f1", "w3"), ("w1", "w4"), ("w3", "w4"),
             ("w4", "w5"), ("w5", "j1"), ("w2", "j1"), ("j1", "d2"), ("f2", "e1"), ("f2", "e2"),
             ("e1", "e3"), ("e3", "j2"), ("e2", "j2"), ("j2", "g1"), ("g1", "g2"), ("g2", "d3"),
             ("g3", "g4"), ("g4", "g5"), ("g5", "e")]:
    b.edge(x, y)
b.edge("d2", "f2", "no")
b.edge("d3", "g3", "yes")


def revision(src, dst):
    xr = dst["x"] + dst["w"] / 2
    xc = xr + 0.07
    return [(src["x"] - src["w"] / 2, src["y"]), (xc, src["y"]), (xc, dst["y"] + 0.06), (xr, dst["y"] + 0.06)]


def more_weeks(d, f):
    xr = 0.1 + 1.5 * len(L) - 0.12
    return [(d["x"] + 0.16, d["y"]), (xr, d["y"]), (xr, f["y"]), (f["x"] + f["w"] / 2, f["y"])]


def returned(d, g):
    xr = g["x"] + g["w"] / 2
    xc = xr + 0.16
    return [(d["x"] - 0.16, d["y"]), (xc, d["y"]), (xc, g["y"]), (xr, g["y"])]


_w5, _w1 = b.nodes["w5"], b.nodes["w1"]
b.edge("w5", "w1", "revision\nrequested", route=revision,
       label_pos=(_w1["x"] + _w1["w"] / 2 + 0.12, (_w1["y"] + _w5["y"]) / 2 + 0.05))
_d2 = b.nodes["d2"]
b.edge("d2", "f1", "yes", route=more_weeks, label_pos=(_d2["x"] + 0.30, _d2["y"] + 0.09))
_g1, _d3 = b.nodes["g1"], b.nodes["d3"]
b.edge("d3", "g1", "no: returned\nwith comment", route=returned,
       label_pos=(_g1["x"] + _g1["w"] / 2 + 0.10, _d3["y"]), label_ha="right")
b.draw("../png/03b_activity_training_grading")
