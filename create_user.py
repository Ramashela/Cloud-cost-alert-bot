"""
One-off CLI helper for creating your first user locally.

Usage:
    python scripts/create_user.py you@example.com --tier free
"""
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app  # noqa: E402
from models import db, User  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("email")
    parser.add_argument("--tier", default="free", choices=["free", "pro", "business"])
    args = parser.parse_args()

    with app.app_context():
        existing = User.query.filter_by(email=args.email).first()
        if existing:
            print(f"User already exists: id={existing.id} tier={existing.tier}")
            return

        user = User(email=args.email, tier=args.tier)
        db.session.add(user)
        db.session.commit()
        print(f"Created user: id={user.id} email={user.email} tier={user.tier}")
        print("\nUse this user_id when creating a cloud account via POST /api/accounts")


if __name__ == "__main__":
    main()
