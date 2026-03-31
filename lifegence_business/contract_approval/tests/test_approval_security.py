# Copyright (c) 2026, Lifegence Corporation and contributors
# For license information, please see license.txt

"""
Security tests for contract approval API: role-based access control.
"""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today, add_days


TEST_GUEST_USER = "test-contract-guest@example.com"


def _ensure_roles():
    """Ensure contract-related roles exist."""
    for role_name in ("Contract Manager", "Contract Approver"):
        if not frappe.db.exists("Role", role_name):
            frappe.get_doc({
                "doctype": "Role",
                "role_name": role_name,
                "desk_access": 1,
            }).insert(ignore_permissions=True)
    frappe.db.commit()


def _ensure_test_user():
    """Create a minimal user with no contract roles."""
    if not frappe.db.exists("User", TEST_GUEST_USER):
        user = frappe.new_doc("User")
        user.email = TEST_GUEST_USER
        user.first_name = "Contract"
        user.last_name = "Guest"
        user.send_welcome_email = 0
        user.insert(ignore_permissions=True)
        frappe.db.commit()


def _create_contract(title="Test Security Contract", **kwargs):
    """Helper to create a test contract."""
    data = {
        "doctype": "Contract",
        "naming_series": "CTR-.YYYY.-",
        "title": title,
        "contract_type": "\u696d\u52d9\u59d4\u8a17\u5951\u7d04",
        "party_name": "Test Party",
        "counterparty_name": "Test Counterparty",
        "start_date": today(),
        "end_date": add_days(today(), 365),
    }
    data.update(kwargs)
    doc = frappe.get_doc(data)
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return doc


class TestApprovalSecurity(FrappeTestCase):
    """Test that approval API endpoints enforce role checks."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        _ensure_roles()
        _ensure_test_user()

    def setUp(self):
        if not frappe.db.exists("Contract Approval Rule", "Test Security Rule"):
            frappe.get_doc({
                "doctype": "Contract Approval Rule",
                "rule_name": "Test Security Rule",
                "is_active": 1,
                "min_amount": 0,
                "max_amount": 99999999,
                "approver_role": "System Manager",
            }).insert(ignore_permissions=True)
            frappe.db.commit()

    def tearDown(self):
        frappe.set_user("Administrator")
        for name in frappe.get_all(
            "Contract",
            filters={"title": ["like", "Test Security Contract%"]},
            pluck="name",
        ):
            frappe.db.delete("Contract Approval Log", {"contract": name})
            frappe.delete_doc("Contract", name, force=True)
        if frappe.db.exists("Contract Approval Rule", "Test Security Rule"):
            frappe.delete_doc("Contract Approval Rule", "Test Security Rule", force=True)
        frappe.db.commit()

    def test_submit_for_approval_requires_contract_manager(self):
        """submit_for_approval should reject users without Contract Manager role."""
        from lifegence_business.contract_approval.api.approval import submit_for_approval

        contract = _create_contract(title="Test Security Contract Submit")
        frappe.set_user(TEST_GUEST_USER)

        with self.assertRaises(frappe.PermissionError):
            submit_for_approval(contract.name)

    def test_approve_contract_requires_contract_approver(self):
        """approve_contract should reject users without Contract Approver role."""
        from lifegence_business.contract_approval.api.approval import (
            submit_for_approval,
            approve_contract,
        )

        contract = _create_contract(title="Test Security Contract Approve")
        submit_for_approval(contract.name)

        frappe.set_user(TEST_GUEST_USER)
        with self.assertRaises(frappe.PermissionError):
            approve_contract(contract.name)

    def test_reject_contract_requires_contract_approver(self):
        """reject_contract should reject users without Contract Approver role."""
        from lifegence_business.contract_approval.api.approval import (
            submit_for_approval,
            reject_contract,
        )

        contract = _create_contract(title="Test Security Contract Reject")
        submit_for_approval(contract.name)

        frappe.set_user(TEST_GUEST_USER)
        with self.assertRaises(frappe.PermissionError):
            reject_contract(contract.name)

    def test_submit_succeeds_for_admin(self):
        """submit_for_approval should work for Administrator."""
        from lifegence_business.contract_approval.api.approval import submit_for_approval

        contract = _create_contract(title="Test Security Contract ManagerOK")
        result = submit_for_approval(contract.name)
        self.assertTrue(result["success"])

    def test_approve_succeeds_for_admin(self):
        """approve_contract should work for Administrator."""
        from lifegence_business.contract_approval.api.approval import (
            submit_for_approval,
            approve_contract,
        )

        contract = _create_contract(title="Test Security Contract ApproverOK")
        submit_for_approval(contract.name)
        result = approve_contract(contract.name)
        self.assertTrue(result["success"])
