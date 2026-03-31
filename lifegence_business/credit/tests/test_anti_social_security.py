# Copyright (c) 2026, Lifegence Corporation and contributors
# For license information, please see license.txt

"""
Security tests for anti-social check API: role-based access control.
"""

import frappe
from frappe.tests.utils import FrappeTestCase


TEST_UNPRIVILEGED_USER = "test-antisocial-noaccess@example.com"


def _ensure_roles():
    for role_name in ("Credit Manager", "Credit Approver"):
        if not frappe.db.exists("Role", role_name):
            frappe.get_doc({
                "doctype": "Role",
                "role_name": role_name,
                "desk_access": 1,
            }).insert(ignore_permissions=True)
    frappe.db.commit()


def _ensure_test_user():
    if not frappe.db.exists("User", TEST_UNPRIVILEGED_USER):
        user = frappe.new_doc("User")
        user.email = TEST_UNPRIVILEGED_USER
        user.first_name = "NoCredit"
        user.last_name = "User"
        user.send_welcome_email = 0
        user.insert(ignore_permissions=True)
        frappe.db.commit()


def _ensure_customer():
    if not frappe.db.exists("Customer", "_Test ASC Security Customer"):
        frappe.get_doc({
            "doctype": "Customer",
            "customer_name": "_Test ASC Security Customer",
            "customer_group": "All Customer Groups",
            "territory": "All Territories",
        }).insert(ignore_permissions=True)
        frappe.db.commit()


class TestAntiSocialSecurity(FrappeTestCase):
    """Test that anti-social check API enforces role checks."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        _ensure_roles()
        _ensure_test_user()
        _ensure_customer()

    def tearDown(self):
        frappe.set_user("Administrator")

    def test_run_check_requires_credit_role(self):
        """run_anti_social_check should reject users without Credit Manager/Approver."""
        from lifegence_business.credit.api.anti_social import run_anti_social_check

        frappe.set_user(TEST_UNPRIVILEGED_USER)
        with self.assertRaises(frappe.PermissionError):
            run_anti_social_check(
                customer="_Test ASC Security Customer",
                check_source="\u81ea\u793e\u8abf\u67fb",
                result="\u554f\u984c\u306a\u3057",
            )

    def test_run_check_succeeds_for_admin(self):
        """run_anti_social_check should work for Administrator."""
        from lifegence_business.credit.api.anti_social import run_anti_social_check

        result = run_anti_social_check(
            customer="_Test ASC Security Customer",
            check_source="\u81ea\u793e\u8abf\u67fb",
            result="\u554f\u984c\u306a\u3057",
        )
        self.assertTrue(result["success"])
