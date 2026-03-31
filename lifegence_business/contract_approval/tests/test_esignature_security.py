# Copyright (c) 2026, Lifegence Corporation and contributors
# For license information, please see license.txt

"""
Security tests for e-signature webhook: signature verification and logging.
"""

import json
from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase


class TestESignatureWebhookSecurity(FrappeTestCase):
    """Test webhook callback security."""

    def test_callback_rejects_missing_envelope(self):
        """Callback should reject envelope_id that doesn't exist in our DB."""
        from lifegence_business.contract_approval.api.esignature import (
            callback_signature_complete,
        )

        payload = {
            "envelope_id": "nonexistent-envelope-id-12345",
            "event_type": "Signed",
            "signer_email": "someone@example.com",
        }

        mock_request = MagicMock()
        mock_request.get_json.return_value = payload
        mock_request.headers = {}
        mock_request.remote_addr = "1.2.3.4"

        with patch.object(frappe, "request", mock_request):
            with self.assertRaises(frappe.ValidationError):
                callback_signature_complete()

    def test_callback_rejects_empty_payload(self):
        """Callback should reject empty payloads."""
        from lifegence_business.contract_approval.api.esignature import (
            callback_signature_complete,
        )

        mock_request = MagicMock()
        mock_request.get_json.return_value = {}
        mock_request.headers = {}
        mock_request.remote_addr = "0.0.0.0"

        with patch.object(frappe, "request", mock_request):
            with self.assertRaises(frappe.ValidationError):
                callback_signature_complete()

    def test_callback_rejects_invalid_event_type(self):
        """Callback should reject invalid event_type values."""
        from lifegence_business.contract_approval.api.esignature import (
            callback_signature_complete,
        )

        payload = {
            "envelope_id": "some-envelope",
            "event_type": "MaliciousAction",
        }

        mock_request = MagicMock()
        mock_request.get_json.return_value = payload
        mock_request.headers = {}
        mock_request.remote_addr = "1.2.3.4"

        with patch.object(frappe, "request", mock_request):
            with self.assertRaises(frappe.ValidationError):
                callback_signature_complete()
