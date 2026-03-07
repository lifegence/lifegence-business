# Copyright (c) 2026, Lifegence Corporation and contributors
# For license information, please see license.txt

"""
Tests for lifegence_contract_approval: Contract CRUD, date validation,
Contract Template, Contract Approval Rule, approval workflow API.
"""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today, add_days


def _create_contract(title="Test Contract", **kwargs):
    """Helper to create a test contract."""
    data = {
        "doctype": "Contract",
        "naming_series": "CTR-.YYYY.-",
        "title": title,
        "contract_type": "業務委託契約",
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


class TestContract(FrappeTestCase):
    """Test Contract DocType."""

    def tearDown(self):
        for name in frappe.get_all("Contract",
                                    filters={"title": ["like", "Test Contract%"]},
                                    pluck="name"):
            frappe.delete_doc("Contract", name, force=True)
        frappe.db.commit()

    def test_create_contract(self):
        """Should create a contract with Draft status."""
        doc = _create_contract()
        self.assertTrue(frappe.db.exists("Contract", doc.name))
        loaded = frappe.get_doc("Contract", doc.name)
        self.assertEqual(loaded.status, "Draft")

    def test_contract_date_validation(self):
        """End date before start date should fail validation."""
        with self.assertRaises(frappe.ValidationError):
            _create_contract(
                title="Test Contract BadDate",
                start_date="2026-06-01",
                end_date="2026-01-01",
            )

    def test_contract_type_options(self):
        """Contract should accept valid contract types."""
        doc = _create_contract(
            title="Test Contract Type",
            contract_type="売買契約",
        )
        self.assertEqual(doc.contract_type, "売買契約")

    def test_contract_amount(self):
        """contract_amount should store currency value."""
        doc = _create_contract(
            title="Test Contract Amount",
            contract_amount=1500000,
        )
        loaded = frappe.get_doc("Contract", doc.name)
        self.assertEqual(float(loaded.contract_amount), 1500000.0)


class TestContractTemplate(FrappeTestCase):
    """Test Contract Template DocType."""

    def tearDown(self):
        for name in frappe.get_all("Contract Template",
                                    filters={"template_name": ["like", "Test Template%"]},
                                    pluck="name"):
            frappe.delete_doc("Contract Template", name, force=True)
        frappe.db.commit()

    def test_create_template(self):
        """Should create a contract template."""
        doc = frappe.get_doc({
            "doctype": "Contract Template",
            "template_name": "Test Template Basic",
            "contract_type": "業務委託契約",
            "is_active": 1,
            "template_content": "Template body content here.",
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()

        self.assertTrue(frappe.db.exists("Contract Template", doc.name))

    def test_template_name_unique(self):
        """template_name should be unique."""
        frappe.get_doc({
            "doctype": "Contract Template",
            "template_name": "Test Template Unique",
            "contract_type": "業務委託契約",
        }).insert(ignore_permissions=True)
        frappe.db.commit()

        with self.assertRaises(frappe.DuplicateEntryError):
            frappe.get_doc({
                "doctype": "Contract Template",
                "template_name": "Test Template Unique",
                "contract_type": "売買契約",
            }).insert(ignore_permissions=True)


class TestContractApprovalRule(FrappeTestCase):
    """Test Contract Approval Rule DocType."""

    def tearDown(self):
        for name in frappe.get_all("Contract Approval Rule",
                                    filters={"rule_name": ["like", "Test Approval Rule%"]},
                                    pluck="name"):
            frappe.delete_doc("Contract Approval Rule", name, force=True)
        frappe.db.commit()

    def test_create_approval_rule(self):
        """Should create an approval rule."""
        doc = frappe.get_doc({
            "doctype": "Contract Approval Rule",
            "rule_name": "Test Approval Rule Basic",
            "is_active": 1,
            "min_amount": 0,
            "max_amount": 1000000,
            "approver_role": "System Manager",
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()

        self.assertTrue(frappe.db.exists("Contract Approval Rule", doc.name))


class TestApprovalWorkflow(FrappeTestCase):
    """Test the approval API workflow."""

    def setUp(self):
        # Create approval rule
        if not frappe.db.exists("Contract Approval Rule", "Test Approval Rule WF"):
            frappe.get_doc({
                "doctype": "Contract Approval Rule",
                "rule_name": "Test Approval Rule WF",
                "is_active": 1,
                "min_amount": 0,
                "max_amount": 99999999,
                "approver_role": "System Manager",
            }).insert(ignore_permissions=True)
            frappe.db.commit()

    def tearDown(self):
        for name in frappe.get_all("Contract",
                                    filters={"title": ["like", "Test Contract WF%"]},
                                    pluck="name"):
            frappe.delete_doc("Contract", name, force=True)
        frappe.db.delete("Contract Approval Log",
                         {"contract": ["like", "CTR-%"]})
        if frappe.db.exists("Contract Approval Rule", "Test Approval Rule WF"):
            frappe.delete_doc("Contract Approval Rule", "Test Approval Rule WF", force=True)
        frappe.db.commit()

    def test_submit_for_approval(self):
        """submit_for_approval should change status to Pending Approval."""
        from lifegence_contract_approval.api.approval import submit_for_approval

        contract = _create_contract(title="Test Contract WF Submit", contract_amount=500000)
        result = submit_for_approval(contract.name)

        self.assertTrue(result["success"])
        reloaded = frappe.get_doc("Contract", contract.name)
        self.assertEqual(reloaded.status, "Pending Approval")

    def test_submit_non_draft_fails(self):
        """submit_for_approval on non-draft contract should fail."""
        from lifegence_contract_approval.api.approval import submit_for_approval

        contract = _create_contract(title="Test Contract WF NonDraft", contract_amount=500000)
        contract.db_set("status", "Approved")
        frappe.db.commit()

        with self.assertRaises(frappe.ValidationError):
            submit_for_approval(contract.name)

    def test_approve_contract(self):
        """approve_contract should set status to Approved."""
        from lifegence_contract_approval.api.approval import (
            submit_for_approval,
            approve_contract,
        )

        contract = _create_contract(title="Test Contract WF Approve", contract_amount=500000)
        submit_for_approval(contract.name)
        result = approve_contract(contract.name, comments="LGTM")

        self.assertTrue(result["success"])
        reloaded = frappe.get_doc("Contract", contract.name)
        self.assertEqual(reloaded.status, "Approved")
        self.assertEqual(reloaded.approved_by, frappe.session.user)

    def test_reject_contract(self):
        """reject_contract should set status to Rejected."""
        from lifegence_contract_approval.api.approval import (
            submit_for_approval,
            reject_contract,
        )

        contract = _create_contract(title="Test Contract WF Reject", contract_amount=500000)
        submit_for_approval(contract.name)
        result = reject_contract(contract.name, comments="Not acceptable")

        self.assertTrue(result["success"])
        reloaded = frappe.get_doc("Contract", contract.name)
        self.assertEqual(reloaded.status, "Rejected")

    def test_approval_creates_log(self):
        """Approval actions should create Contract Approval Log entries."""
        from lifegence_contract_approval.api.approval import submit_for_approval

        contract = _create_contract(title="Test Contract WF Log", contract_amount=500000)
        submit_for_approval(contract.name)

        logs = frappe.get_all(
            "Contract Approval Log",
            filters={"contract": contract.name},
            fields=["action", "action_by"],
        )
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].action, "Submitted for Approval")
