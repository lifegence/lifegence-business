"""E2E test data seed.

Usage:
    bench --site dev.localhost execute lifegence_agent.scripts.seed_e2e.run
"""
from __future__ import annotations

import frappe


TEST_USERS = [
    {
        "email": "e2e-user1@lifegence.test",
        "first_name": "E2E",
        "last_name": "User1",
        "password": "e2etest123",
        "roles": ["System Manager", "Chat User"],
    },
    {
        "email": "e2e-user2@lifegence.test",
        "first_name": "E2E",
        "last_name": "User2",
        "password": "e2etest123",
        "roles": ["System Manager", "Chat User"],
    },
]


def _upsert_user(spec: dict) -> str:
    email = spec["email"]
    if frappe.db.exists("User", email):
        user = frappe.get_doc("User", email)
    else:
        user = frappe.new_doc("User")
        user.email = email
        user.send_welcome_email = 0

    user.first_name = spec["first_name"]
    user.last_name = spec["last_name"]
    user.enabled = 1
    user.new_password = spec["password"]

    existing_roles = {r.role for r in (user.roles or [])}
    for role in spec["roles"]:
        if role in existing_roles:
            continue
        if not frappe.db.exists("Role", role):
            continue
        user.append("roles", {"role": role})

    user.flags.ignore_password_policy = True
    user.flags.ignore_permissions = True
    user.save(ignore_permissions=True)
    return email


def run() -> None:
    """Seed idempotent E2E test fixtures."""
    print("→ Seeding E2E test users…")
    for spec in TEST_USERS:
        email = _upsert_user(spec)
        print(f"  ✓ User: {email}")

    frappe.db.commit()
    print("✓ Seed complete")


if __name__ == "__main__":
    run()
