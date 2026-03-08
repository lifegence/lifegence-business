# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestCreditCheck(FrappeTestCase):
	"""Integration test for SO credit check and API endpoints."""

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
		if not frappe.db.exists("Customer", "_Test CC Customer"):
			frappe.get_doc({
				"doctype": "Customer",
				"customer_name": "_Test CC Customer",
				"customer_group": "All Customer Groups",
				"territory": "All Territories",
			}).insert(ignore_permissions=True)
		frappe.db.commit()

	@classmethod
	def _ensure_settings(cls):
		settings = frappe.get_single("Credit Settings")
		if not settings.default_credit_period_days:
			settings.default_credit_period_days = 365
			settings.auto_block_on_exceed = 1
			settings.alert_threshold_pct = 80
			settings.review_cycle_months = 12
			settings.grade_a_min_score = 80
			settings.grade_b_min_score = 60
			settings.grade_c_min_score = 40
			settings.grade_d_min_score = 20
			settings.send_review_reminder_days = 30
			settings.save(ignore_permissions=True)
		frappe.db.commit()

	def _get_test_company(self):
		return frappe.db.get_value("Company", {}, "name") or "_Test Company"

	def _create_credit_limit(self, amount=5000000):
		company = self._get_test_company()
		existing = frappe.db.get_value(
			"Credit Limit",
			{"customer": "_Test CC Customer", "company": company},
			"name",
		)
		if existing:
			frappe.delete_doc("Credit Limit", existing, force=True)

		return frappe.get_doc({
			"doctype": "Credit Limit",
			"customer": "_Test CC Customer",
			"company": company,
			"credit_limit_amount": amount,
			"status": "Active",
		}).insert(ignore_permissions=True)

	def test_api_get_credit_status(self):
		"""Test credit status API."""
		self._create_credit_limit()
		from lifegence_business.credit.api.credit_status import get_credit_status

		result = get_credit_status(customer="_Test CC Customer")
		self.assertTrue(result["success"])
		self.assertEqual(result["credit_status"]["credit_limit_amount"], 5000000)

	def test_api_get_credit_status_not_found(self):
		"""Test credit status API with non-existent customer."""
		from lifegence_business.credit.api.credit_status import get_credit_status

		result = get_credit_status(customer="NONEXISTENT")
		self.assertFalse(result["success"])

	def test_credit_check_suspended_limit(self):
		"""Test that suspended credit limit blocks SO."""
		cl = self._create_credit_limit()
		cl.status = "Suspended"
		cl.suspension_reason = "テスト停止"
		cl.save(ignore_permissions=True)

		# Simulate SO document
		class MockDoc:
			customer = "_Test CC Customer"
			company = cl.company
			grand_total = 100000
			name = "SO-TEST-001"
			credit_check_passed = 0
			credit_check_note = ""

		from lifegence_business.credit.services.credit_check import check_credit_on_sales_order

		self.assertRaises(
			frappe.ValidationError,
			check_credit_on_sales_order,
			MockDoc(),
		)

	def test_risk_scoring_service(self):
		"""Test standalone risk scoring service."""
		from lifegence_business.credit.services.risk_scoring import calculate_risk_score

		result = calculate_risk_score(
			revenue=100000000,
			profit=10000000,
			capital=50000000,
			years_in_business=15,
			payment_history_score=90,
			existing_transaction_months=36,
			average_monthly_transaction=2000000,
		)
		self.assertIn("score", result)
		self.assertIn("grade", result)
		self.assertIn("recommended_limit", result)
		self.assertGreaterEqual(result["score"], 80)
