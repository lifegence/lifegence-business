# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestCreditLimit(FrappeTestCase):
	"""Test cases for Credit Limit DocType."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls._ensure_roles()
		cls._ensure_customer()
		cls._ensure_company()
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
		if not frappe.db.exists("Customer", "_Test CL Customer"):
			frappe.get_doc({
				"doctype": "Customer",
				"customer_name": "_Test CL Customer",
				"customer_group": "All Customer Groups",
				"territory": "All Territories",
			}).insert(ignore_permissions=True)
		frappe.db.commit()

	@classmethod
	def _ensure_company(cls):
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

	def _create_credit_limit(self, customer="_Test CL Customer", **kwargs):
		company = kwargs.pop("company", self._get_test_company())
		# Delete existing if any
		existing = frappe.db.get_value(
			"Credit Limit",
			{"customer": customer, "company": company},
			"name",
		)
		if existing:
			frappe.delete_doc("Credit Limit", existing, force=True)

		defaults = {
			"doctype": "Credit Limit",
			"customer": customer,
			"company": company,
			"credit_limit_amount": 5000000,
			"status": "Active",
		}
		defaults.update(kwargs)
		doc = frappe.get_doc(defaults)
		doc.insert(ignore_permissions=True)
		return doc

	def test_create_credit_limit(self):
		"""Test basic credit limit creation."""
		doc = self._create_credit_limit()
		self.assertEqual(doc.customer, "_Test CL Customer")
		self.assertEqual(doc.credit_limit_amount, 5000000)
		self.assertEqual(doc.status, "Active")

	def test_balance_calculation(self):
		"""Test used_amount calculation is 0 when no SO/SI exist."""
		doc = self._create_credit_limit()
		self.assertEqual(doc.used_amount, 0)
		self.assertEqual(doc.available_amount, 5000000)
		self.assertEqual(doc.usage_percentage, 0)

	def test_duplicate_check(self):
		"""Test that duplicate customer+company is prevented."""
		self._create_credit_limit()
		self.assertRaises(
			frappe.ValidationError,
			self._create_credit_limit,
		)

	def test_check_credit_within_limit(self):
		"""Test credit check when within limit."""
		doc = self._create_credit_limit(credit_limit_amount=10000000)
		result = doc.check_credit(additional_amount=1000000)
		self.assertTrue(result["allowed"])

	def test_check_credit_exceed_limit(self):
		"""Test credit check when exceeding limit."""
		doc = self._create_credit_limit(credit_limit_amount=1000000)
		result = doc.check_credit(additional_amount=2000000)
		self.assertFalse(result["allowed"])
		self.assertIn("excess", result)

	def test_api_update_credit_limit(self):
		"""Test credit limit update via API."""
		doc = self._create_credit_limit()
		from lifegence_credit.api.credit_limit import update_credit_limit

		result = update_credit_limit(
			customer="_Test CL Customer",
			new_amount=8000000,
			change_reason="増額承認",
			company=self._get_test_company(),
			change_detail="テスト増額",
		)
		self.assertTrue(result["success"])
		self.assertEqual(result["new_amount"], 8000000)
		self.assertIn("history", result)
