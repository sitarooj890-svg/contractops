from .database import SessionLocal
from .models import Membership, Organization, User
from .security import hash_password

ORG_NAME = "Demo Org"
PASSWORD = "Test1234!"
USERS = [
    ("analyst@test.com", "Analyst Tester", "analyst"),
    ("approver@test.com", "Approver Tester", "approver"),
    ("admin@test.com", "Admin Tester", "admin"),
]


def seed() -> None:
    db = SessionLocal()
    try:
        org = db.query(Organization).filter_by(name=ORG_NAME).first()
        if org is None:
            org = Organization(name=ORG_NAME)
            db.add(org)
            db.flush()
            print(f"Created organization {ORG_NAME!r}")
        else:
            print(f"Organization {ORG_NAME!r} already exists")

        for email, full_name, role in USERS:
            user = db.query(User).filter_by(email=email).first()
            if user is None:
                user = User(
                    email=email,
                    password_hash=hash_password(PASSWORD),
                    full_name=full_name,
                )
                db.add(user)
                db.flush()
                print(f"Created user {email} ({role})")
            else:
                print(f"User {email} already exists")

            membership = (
                db.query(Membership)
                .filter_by(user_id=user.id, organization_id=org.id)
                .first()
            )
            if membership is None:
                db.add(
                    Membership(
                        user_id=user.id, organization_id=org.id, role=role
                    )
                )
                print(f"Created membership {email} -> {role}")
            else:
                print(f"Membership {email} -> {membership.role} already exists")

        db.commit()
        print("Seed complete")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
