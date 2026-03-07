# Copyright (c) 2026, Lifegence Corporation and contributors
# For license information, please see license.txt

"""
Tests for e-signature functionality: Provider Settings, E-Signature Request,
E-Signature Log, and esignature API.
"""

import json

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today, add_days


def _create_provider(name="Test Provider", **kwargs):
    """Helper to create a test e-signature provider settings."""
    data = {
        "doctype": "E-Signature Provider Settings",
        "provider_name": name,
        "provider_type": "CloudSign",
        "api_key": "test-api-key-12345",
        "api_endpoint": "https://api.test-cloudsign.example.com/v1",
        "enabled": 1,
        "sandbox_mode": 1,
        "default_expiry_days": 30,
    }
    data.update(kwargs)
    doc = frappe.get_doc(data)
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return doc


def _create_contract(title="Test ES Contract", status="Approved", **kwargs):
    """Helper to create a test contract with specified status."""
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
    if status != "Draft":
        doc.db_set("status", status)
    frappe.db.commit()
    return doc


_VALID_SIGNERS = json.dumps([
    {"name": "Taro Yamada", "email": "taro@example.com", "order": 1},
    {"name": "Hanako Sato", "email": "hanako@example.com", "order": 2},
])


class TestESignatureProviderSettings(FrappeTestCase):
    """Test E-Signature Provider Settings DocType."""

    def tearDown(self):
        for name in frappe.get_all(
            "E-Signature Provider Settings",
            filters={"provider_name": ["like", "Test Provider%"]},
            pluck="name",
        ):
            frappe.delete_doc("E-Signature Provider Settings", name, force=True)
        frappe.db.commit()

    def test_create_provider_settings(self):
        """TC-ES01: Should create provider settings with required fields."""
        doc = _create_provider()
        self.assertTrue(frappe.db.exists("E-Signature Provider Settings", doc.name))
        loaded = frappe.get_doc("E-Signature Provider Settings", doc.name)
        self.assertEqual(loaded.provider_type, "CloudSign")
        self.assertEqual(loaded.enabled, 1)
        self.assertEqual(loaded.sandbox_mode, 1)

    def test_provider_api_endpoint_https(self):
        """TC-ES02: API endpoint must use HTTPS."""
        with self.assertRaises(frappe.ValidationError):
            _create_provider(
                name="Test Provider HTTP",
                api_endpoint="http://insecure.example.com/v1",
            )


class TestESignatureRequest(FrappeTestCase):
    """Test E-Signature Request DocType."""

    def setUp(self):
        # Create provider
        if not frappe.db.exists("E-Signature Provider Settings", "Test Provider ES"):
            _create_provider(name="Test Provider ES")

    def tearDown(self):
        # Clean up requests
        for name in frappe.get_all("E-Signature Request", pluck="name"):
            # Delete associated logs first
            frappe.db.delete("E-Signature Log", {"signature_request": name})
            frappe.delete_doc("E-Signature Request", name, force=True)
        # Clean up contracts
        for name in frappe.get_all(
            "Contract",
            filters={"title": ["like", "Test ES Contract%"]},
            pluck="name",
        ):
            frappe.delete_doc("Contract", name, force=True)
        # Clean up provider
        if frappe.db.exists("E-Signature Provider Settings", "Test Provider ES"):
            frappe.delete_doc("E-Signature Provider Settings", "Test Provider ES", force=True)
        frappe.db.commit()

    def test_create_signature_request(self):
        """TC-ES03: Should create a signature request in Draft status."""
        contract = _create_contract(title="Test ES Contract Create")
        doc = frappe.get_doc({
            "doctype": "E-Signature Request",
            "contract": contract.name,
            "provider": "Test Provider ES",
            "status": "Draft",
            "signers": _VALID_SIGNERS,
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()

        self.assertTrue(frappe.db.exists("E-Signature Request", doc.name))
        loaded = frappe.get_doc("E-Signature Request", doc.name)
        self.assertEqual(loaded.status, "Draft")
        self.assertEqual(loaded.requested_by, frappe.session.user)

    def test_request_requires_approved_contract(self):
        """TC-ES04: Should reject request for non-approved contracts."""
        contract = _create_contract(title="Test ES Contract Draft", status="Draft")

        with self.assertRaises(frappe.ValidationError):
            frappe.get_doc({
                "doctype": "E-Signature Request",
                "contract": contract.name,
                "provider": "Test Provider ES",
                "signers": _VALID_SIGNERS,
            }).insert(ignore_permissions=True)

    def test_request_validates_signers_json(self):
        """TC-ES05: Should validate signers JSON format."""
        contract = _create_contract(title="Test ES Contract JSON")

        # Invalid JSON
        with self.assertRaises(frappe.ValidationError):
            frappe.get_doc({
                "doctype": "E-Signature Request",
                "contract": contract.name,
                "provider": "Test Provider ES",
                "signers": "not valid json",
            }).insert(ignore_permissions=True)

    def test_send_signature_request_api(self):
        """TC-ES06: API should create request and change status to Sent."""
        from lifegence_business.contract_approval.api.esignature import create_signature_request

        contract = _create_contract(title="Test ES Contract Send")
        result = create_signature_request(
            contract_name=contract.name,
            signers=_VALID_SIGNERS,
            provider_name="Test Provider ES",
        )

        self.assertTrue(result["success"])
        self.assertIn("signature_request", result)
        self.assertIn("envelope_id", result)

        loaded = frappe.get_doc("E-Signature Request", result["signature_request"])
        self.assertEqual(loaded.status, "Sent")
        self.assertIsNotNone(loaded.sent_date)
        self.assertIsNotNone(loaded.envelope_id)

    def test_check_signature_status(self):
        """TC-ES07: Should return status for a signature request."""
        from lifegence_business.contract_approval.api.esignature import (
            create_signature_request,
            check_signature_status,
        )

        contract = _create_contract(title="Test ES Contract Status")
        create_result = create_signature_request(
            contract_name=contract.name,
            signers=_VALID_SIGNERS,
            provider_name="Test Provider ES",
        )

        result = check_signature_status(
            signature_request_name=create_result["signature_request"],
        )

        self.assertTrue(result["success"])
        self.assertTrue(result["found"])
        self.assertEqual(result["status"], "Sent")
        self.assertEqual(result["contract"], contract.name)
        self.assertIsInstance(result["signers"], list)
        self.assertEqual(len(result["signers"]), 2)

    def test_duplicate_request_prevention(self):
        """TC-ES10: Should prevent duplicate active requests for same contract."""
        from lifegence_business.contract_approval.api.esignature import create_signature_request

        contract = _create_contract(title="Test ES Contract Dup")
        create_signature_request(
            contract_name=contract.name,
            signers=_VALID_SIGNERS,
            provider_name="Test Provider ES",
        )

        # Second request should fail
        with self.assertRaises(frappe.ValidationError):
            create_signature_request(
                contract_name=contract.name,
                signers=_VALID_SIGNERS,
                provider_name="Test Provider ES",
            )


class TestESignatureLog(FrappeTestCase):
    """Test E-Signature Log DocType."""

    def setUp(self):
        if not frappe.db.exists("E-Signature Provider Settings", "Test Provider Log"):
            _create_provider(name="Test Provider Log")

    def tearDown(self):
        for name in frappe.get_all("E-Signature Request", pluck="name"):
            frappe.db.delete("E-Signature Log", {"signature_request": name})
            frappe.delete_doc("E-Signature Request", name, force=True)
        for name in frappe.get_all(
            "Contract",
            filters={"title": ["like", "Test ES Contract%"]},
            pluck="name",
        ):
            frappe.delete_doc("Contract", name, force=True)
        if frappe.db.exists("E-Signature Provider Settings", "Test Provider Log"):
            frappe.delete_doc("E-Signature Provider Settings", "Test Provider Log", force=True)
        frappe.db.commit()

    def test_signature_log_creation(self):
        """TC-ES08: Sending a request should create a log entry."""
        from lifegence_business.contract_approval.api.esignature import create_signature_request

        contract = _create_contract(title="Test ES Contract Log")
        result = create_signature_request(
            contract_name=contract.name,
            signers=_VALID_SIGNERS,
            provider_name="Test Provider Log",
        )

        logs = frappe.get_all(
            "E-Signature Log",
            filters={"signature_request": result["signature_request"]},
            fields=["event_type", "event_date"],
        )
        self.assertGreaterEqual(len(logs), 1)
        self.assertEqual(logs[0].event_type, "Sent")

    def test_signature_log_append_only(self):
        """TC-ES09: Log entries should be append-only (no modification)."""
        from lifegence_business.contract_approval.api.esignature import create_signature_request

        contract = _create_contract(title="Test ES Contract LogAppend")
        result = create_signature_request(
            contract_name=contract.name,
            signers=_VALID_SIGNERS,
            provider_name="Test Provider Log",
        )

        logs = frappe.get_all(
            "E-Signature Log",
            filters={"signature_request": result["signature_request"]},
            pluck="name",
        )
        self.assertTrue(len(logs) > 0)

        log_doc = frappe.get_doc("E-Signature Log", logs[0])
        log_doc.event_type = "Error"
        with self.assertRaises(frappe.ValidationError):
            log_doc.save()
