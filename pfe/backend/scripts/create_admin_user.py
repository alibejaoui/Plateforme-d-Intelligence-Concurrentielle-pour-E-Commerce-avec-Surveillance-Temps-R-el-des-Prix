"""
One-off script: create (or reset) the default admin user. Not run on app startup.

From the backend directory:
  python scripts/create_admin_user.py
  python scripts/create_admin_user.py --reset   # set password + role even if user exists

Requires DATABASE_URL / MySQL to match your application configuration.
Uses the same password hashing as the application (get_password_hash).
"""
import argparse
import sys
from pathlib import Path

# Add backend root (parent of `app`) to path when run as a script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal  # noqa: E402
from app.core.security import get_password_hash  # noqa: E402
from app.models.user import User  # noqa: E402

ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "Admin123!"


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or reset default admin user.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="If the user already exists, update password and role to admin (fixes wrong password).",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        if not user:
            admin = User(
                email=ADMIN_EMAIL,
                hashed_password=get_password_hash(ADMIN_PASSWORD),
                full_name="admin",
                is_active=True,
                is_superuser=False,
                role="admin",
            )
            db.add(admin)
            db.commit()
            print("Created admin user:", ADMIN_EMAIL)
            return

        if args.reset:
            user.hashed_password = get_password_hash(ADMIN_PASSWORD)
            user.role = "admin"
            user.is_active = True
            db.add(user)
            db.commit()
            print("Updated admin password and role for:", ADMIN_EMAIL)
            return

        print(
            "Admin user already exists; skipping.\n"
            "If login fails with the expected password, run:\n"
            f"  python scripts/create_admin_user.py --reset"
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
