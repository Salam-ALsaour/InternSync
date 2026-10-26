"""Deploy the API to a Hugging Face Space (Increment 2 design, Section 10; docs/Deployment.md). Run by
.github/workflows/deploy-api.yml; it can also be run by hand from backend/:

    HF_TOKEN=... HF_SPACE=owner/internsync-api WEB_URL=https://internsync.vercel.app python scripts/deploy_space.py

It creates the Space if needed (Docker, public: the web app must reach it), copies the settings and the secrets that
are present in the environment into the Space, and uploads the files the image is built from. Secret values are
never printed."""
import os
import shutil
import sys
import tempfile
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
FILES = ["Dockerfile", "requirements.txt", "requirements-ai.txt", "alembic.ini", "pyproject.toml"]
FOLDERS = ["alembic", "app"]
README = """---
title: InternSync API
emoji: 🎓
colorFrom: green
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

The API of InternSync, the internship management platform (CSC 305, Imam Abdulrahman Bin Faisal University).
Deployed from GitHub; do not edit the files here.
"""
# Settings of the reference deployment that are not secret.
VARIABLES = {"ENV": "production", "PORT": "7860", "STORAGE_BACKEND": "supabase", "SCHEDULER_ENABLED": "true",
             "SMTP_HOST": "smtp.gmail.com", "SMTP_PORT": "587", "SMTP_TLS": "true", "FORWARDED_ALLOW_IPS": "*"}
SECRETS = ["DATABASE_URL", "JWT_SECRET", "SUPABASE_URL", "SUPABASE_SERVICE_KEY", "SMTP_USER", "SMTP_PASSWORD"]


def space_url(space: str) -> str:
    """The address a Space is served at: owner-name.hf.space, lower case, with _ and . turned into -."""
    host = space.replace("/", "-").replace("_", "-").replace(".", "-").lower()
    return f"https://{host}.hf.space"


def stage(to: Path) -> None:
    for name in FILES:
        shutil.copy2(BACKEND / name, to / name)
    for name in FOLDERS:
        shutil.copytree(BACKEND / name, to / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    (to / "README.md").write_text(README, encoding="utf-8")


def main() -> int:
    token, space = os.environ.get("HF_TOKEN", ""), os.environ.get("HF_SPACE", "")
    if not token or not space:
        print("HF_TOKEN and HF_SPACE are required.", file=sys.stderr)
        return 2
    from huggingface_hub import HfApi

    api = HfApi(token=token)
    api.create_repo(space, repo_type="space", space_sdk="docker", private=False, exist_ok=True)

    variables = dict(VARIABLES)
    web = os.environ.get("WEB_URL", "").rstrip("/")
    if web:
        variables.update(FRONTEND_BASE_URL=web, CORS_ORIGINS=web)
    if os.environ.get("SMTP_USER"):
        variables["MAIL_FROM"] = f"InternSync <{os.environ['SMTP_USER']}>"
    for key, value in variables.items():
        api.add_space_variable(space, key, value)
    present = [key for key in SECRETS if os.environ.get(key)]
    for key in present:
        api.add_space_secret(space, key, os.environ[key])
    missing = sorted(set(SECRETS) - set(present))
    print(f"settings: {len(variables)} variables; secrets updated: {', '.join(present) or 'none'}")
    if missing:
        print(f"secrets not in this run (kept as they are in the Space): {', '.join(missing)}")

    with tempfile.TemporaryDirectory() as tmp:
        stage(Path(tmp))
        sha = os.environ.get("GITHUB_SHA", "local")[:12]
        api.upload_folder(repo_id=space, repo_type="space", folder_path=tmp, commit_message=f"Deploy {sha}",
                          delete_patterns=["app/**", "alembic/**"])
    print(f"uploaded; the Space rebuilds the image now: {space_url(space)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
