# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestCreditAlert(FrappeTestCase):
	"""Test cases for Credit Alert DocType."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls._ensure_roles()
		cls._ensure_customer()
		cls._ensure_settings()

	@classmethod
	def _ensure_roles(cls):
		for role_name in ("Credit Manager", "Credit Approver"):
			if not frappe.db.exists("Role", role_name):
				frappe.get_doc({
					"doctype": "Role",
					"role_name": role_name,
					"desk_access": 1,
				}).insert(ignore_permissions=True)

	@classmethod
	def _ensure_customer(cls):
		if not frappe.db.exists("Customer", "_Test Alert Customer"):
			frappe.get_doc({
				"doctype": "Customer",
				"customer_name": "_Test Alert Customer",
				"customer_group": "All Customer Groups",
				"territory": "All Territories",
			}).insert(ignore_permissions=True)
		frappe.db.commit()

	@classmethod
	def _ensure_settings(cls):
		settings = frappe.get_single("Credit Settings")
		if not settings.default_credit_period_days:
			settings.default_credit_period_days = 365
			settings.save(ignore_permissions=True)
		frappe.db.commit()

	def _create_alert(self, **kwargs):
		defaults = {
			"doctype": "Credit Alert",
			"customer": "_Test Alert Customer",
			"alert_type": "限度額超過",
			"severity": "Critical",
			"alert_message": "テストアラート",
		}
		defaults.update(kwargs)
		doc = frappe.get_doc(defaults)
		doc.insert(ignore_permissions=True)
		return doc

	def test_create_alert(self):
		"""Test basic alert creation."""
		doc = self._create_alert()
		self.assertEqual(doc.status, "Open")
		self.assertEqual(doc.alert_type, "限度額超過")
		self.assertEqual(doc.severity, "Critical")

	def test_alert_excess_calculation(self):
		"""Test excess_amount auto-calculation."""
		doc = self._create_alert(
			threshold_value=5000000,
			current_value=6500000,
		)
		self.assertEqual(doc.excess_amount, 1500000)

	def test_alert_status_transitions(self):
		"""Test alert status transitions."""
		doc = self._create_alert()
		self.assertEqual(doc.status, "Open")

		doc.status = "Acknowledged"
		doc.acknowledged_by = frappe.session.user
		doc.save(ignore_permissions=True)
		self.assertEqual(doc.status, "Acknowledged")

		doc.status = "Resolved"
		doc.resolved_by = frappe.session.user
		doc.resolution_note = "解決済み"
		doc.save(ignore_permissions=True)
		self.assertEqual(doc.status, "Resolved")

	def test_no_duplicate_open_alerts(self):
		"""Test that duplicate open alerts are prevented by alert_generator."""
		from lifegence_credit.credit.services.balance_calculator import _create_alert_if_not_exists

		# Create first alert
		_create_alert_if_not_exists(
			customer="_Test Alert Customer",
			company=None,
			alert_type="支払遅延",
			severity="High",
			message="テスト遅延アラート",
		)

		count_before = frappe.db.count(
			"Credit Alert",
			{"customer": "_Test Alert Customer", "alert_type": "支払遅延", "status": "Open"},
		)

		# Try to create duplicate
		_create_alert_if_not_exists(
			customer="_Test Alert Customer",
			company=None,
			alert_type="支払遅延",
			severity="High",
			message="テスト遅延アラート（重複）",
		)

		count_after = frappe.db.count(
			"Credit Alert",
			{"customer": "_Test Alert Customer", "alert_type": "支払遅延", "status": "Open"},
		)
		self.assertEqual(count_before, count_after)
