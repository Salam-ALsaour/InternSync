"""Operator commands (Increment 1 design, Section 9).

    python -m app.cli create-platform-admin --email admin@example.org --name-en "..." --name-ar "..."
    python -m app.cli run-job flag_missing
    python -m app.cli vapid-keys          # a key pair for web push (FR-PWA-02)

The password is read from the INTERNSYNC_ADMIN_PASSWORD environment variable or asked for on the terminal;
it is never passed on the command line."""
import argparse
import getpass
import os
import sys

from sqlalchemy import func, select

from app.core import audit, clock
from app.core.db import SessionLocal
from app.core.security import hash_password, password_is_strong
from app.jobs import jobs
from app.models import User


def create_platform_admin(email: str, name_en: str, name_ar: str) -> int:
    password = os.environ.get("INTERNSYNC_ADMIN_PASSWORD") or getpass.getpass("Password: ")
    if not password_is_strong(password):
        print("The password needs at least 8 characters with letters and digits.", file=sys.stderr)
        return 2
    with SessionLocal() as db:
        if db.scalar(select(User.id).where(func.lower(User.email) == email.strip().lower())):
            print(f"An account with {email} already exists.", file=sys.stderr)
            return 1
        now = clock.now()
        user = User(email=email.strip(), password_hash=hash_password(password), role="platform_admin",
                    name_en=name_en, name_ar=name_ar, email_confirmed_at=now, verification_status="not_required")
        db.add(user)
        db.flush()
        audit.record(db, None, "create", "user", user.id, new={"role": "platform_admin", "email": user.email})
        db.commit()
    print(f"Platform Admin {email} created.")
    return 0


def vapid_keys() -> int:
    """Print a new VAPID key pair: the public key in the form browsers expect, the private key as raw base64url."""
    import base64

    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec

    key = ec.generate_private_key(ec.SECP256R1())
    raw = key.private_numbers().private_value.to_bytes(32, "big")
    public = key.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)

    def b64(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode()
    print(f"VAPID_PUBLIC_KEY={b64(public)}")
    print(f"VAPID_PRIVATE_KEY={b64(raw)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    admin = sub.add_parser("create-platform-admin", help="create the first Platform Admin account")
    admin.add_argument("--email", required=True)
    admin.add_argument("--name-en", required=True)
    admin.add_argument("--name-ar", required=True)
    job = sub.add_parser("run-job", help="run one scheduled job now")
    job.add_argument("name", choices=sorted(jobs.JOBS))
    sub.add_parser("vapid-keys", help="print a new key pair for web push")
    args = parser.parse_args(argv)
    if args.command == "vapid-keys":
        return vapid_keys()
    if args.command == "create-platform-admin":
        return create_platform_admin(args.email, args.name_en, args.name_ar)
    jobs.run(SessionLocal, args.name)
    print(f"{args.name} finished; see job_runs for the result.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
