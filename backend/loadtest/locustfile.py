"""Load test of NFR-PER-01 (Increment 4, RQ-9): 95% of ordinary requests within 2 s with 50 concurrent users.

    pip install -r backend/loadtest/requirements.txt
    locust -f backend/loadtest/locustfile.py --host http://localhost:8000 --headless -u 50 -r 5 -t 5m \
        --csv results/load

Runs against the Docker stack with the demo data (`python -m app.seed --demo`). Each simulated user signs in as one
of the demo roles and repeats what that role does most: open the dashboard, open lists, open a record, and, for the
student, save a report draft. Demo accounts exist only outside production, so the reference deployment needs its
own test accounts (the `LOAD_USERS` variable: `email:password,email:password`)."""
import itertools
import os
import random

from locust import HttpUser, between, task

PASSWORD = "Demo-2026-pass"
DEMO = ["s1@iau.edu.sa", "omar@nakheel.example", "f.alharbi@iau.edu.sa", "coordinator@iau.edu.sa",
        "sara@nakheel.example"]
USERS = [tuple(u.split(":", 1)) for u in os.environ["LOAD_USERS"].split(",")] if os.environ.get("LOAD_USERS") \
    else [(email, PASSWORD) for email in DEMO]
_next = itertools.cycle(USERS)


class Visitor(HttpUser):
    wait_time = between(1, 3)

    def on_start(self) -> None:
        email, password = next(_next)
        r = self.client.post("/api/v1/auth/login", json={"email": email, "password": password}, name="login")
        r.raise_for_status()
        body = r.json()
        self.client.headers["Authorization"] = f"Bearer {body['access_token']}"
        self.role = body["user"]["role"]
        self.placements = [p["id"] for p in self.client.get("/api/v1/placements?page_size=20",
                                                            name="/placements").json().get("items", [])] \
            if self.role != "platform_admin" else []
        self.slot = None
        if self.role == "student" and self.placements:
            slots = self.client.get(f"/api/v1/placements/{self.placements[0]}/report-slots",
                                    name="/placements/{id}/report-slots").json()
            self.slot = next((s["id"] for s in slots if s["status"] == "draft"), None)

    @task(5)
    def dashboard(self) -> None:
        self.client.get("/api/v1/dashboard", name="/dashboard")

    @task(2)
    def notifications(self) -> None:
        self.client.get("/api/v1/notifications?unread_only=true&page_size=1", name="/notifications")

    @task(3)
    def lists(self) -> None:
        if self.role == "student":
            self.client.get("/api/v1/vacancies?page_size=20", name="/vacancies")
        elif self.role == "coordinator":
            self.client.get("/api/v1/grades", name="/grades")
            self.client.get("/api/v1/cycles", name="/cycles")
        else:
            self.client.get("/api/v1/placements?page_size=20", name="/placements")

    @task(3)
    def record(self) -> None:
        if self.placements:
            pid = random.choice(self.placements)
            self.client.get(f"/api/v1/placements/{pid}/report-slots", name="/placements/{id}/report-slots")
            if self.role in ("company_supervisor", "academic_supervisor", "coordinator"):
                self.client.get(f"/api/v1/placements/{pid}/attendance", name="/placements/{id}/attendance")

    @task(1)
    def save_draft(self) -> None:
        if self.slot:
            self.client.put(f"/api/v1/report-slots/{self.slot}/draft", name="/report-slots/{id}/draft", json={
                "tasks_performed": "Load test", "learning": "Load test", "challenges": "Load test",
                "next_week_plan": "Load test"})
