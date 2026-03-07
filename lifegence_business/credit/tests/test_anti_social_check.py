# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, nowdate


class TestAntiSocialCheck(FrappeTestCase):
	"""Test cases for Anti-Social Check DocType."""

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
		if not frappe.db.exists("Customer", "_Test ASC Customer"):
			frappe.get_doc({
				"doctype": "Customer",
				"customer_name": "_Test ASC Customer",
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

	def _create_check(self, **kwargs):
		defaults = {
			"doctype": "Anti-Social Check",
			"customer": "_Test ASC Customer",
			"check_source": "自社調査",
			"result": "問題なし",
			"checked_by": "Administrator",
			"check_date": nowdate(),
		}
		defaults.update(kwargs)
		doc = frappe.get_doc(defaults)
		doc.insert(ignore_permissions=True)
		return doc

	def test_create_check(self):
		"""Test basic anti-social check creation."""
		doc = self._create_check()
		self.assertEqual(doc.customer, "_Test ASC Customer")
		self.assertEqual(doc.result, "問題なし")
		self.assertIsNotNone(doc.valid_until)

	def test_auto_valid_until(self):
		"""Test valid_until is auto-set to check_date + 1 year."""
		doc = self._create_check(check_date="2026-01-01")
		expected = add_days("2026-01-01", 365)
		self.assertEqual(str(doc.valid_until), str(expected))

	def test_customer_field_update(self):
		"""Test that Customer.anti_social_check_result is updated."""
		self._create_check(result="問題なし")
		result = frappe.db.get_value("Customer", "_Test ASC Customer", "anti_social_check_result")
		self.assertEqual(result, "問題なし")

	def test_result_match_positive(self):
		"""Test 該当あり result triggers suspension."""
		# Create a credit limit first
		company = frappe.db.get_value("Company", {}, "name") or "_Test Company"
		existing = frappe.db.get_value(
			"Credit Limit",
			{"customer": "_Test ASC Customer", "company": company},
			"name",
		)
		if existing:
			frappe.delete_doc("Credit Limit", existing, force=True)

		frappe.get_doc({
			"doctype": "Credit Limit",
			"customer": "_Test ASC Customer",
			"company": company,
			"credit_limit_amount": 5000000,
			"status": "Active",
		}).insert(ignore_permissions=True)

		# Create 該当あり check
		self._create_check(result="該当あり")

		# Verify credit limit was suspended
		status = frappe.db.get_value(
			"Credit Limit",
			{"customer": "_Test ASC Customer", "company": company},
			"status",
		)
		self.assertEqual(status, "Suspended")

	def test_api_get_check_status(self):
		"""Test API to get check status."""
		self._create_check()
		from lifegence_business.credit.api.anti_social import get_check_status

		result = get_check_status(customer="_Test ASC Customer")
		self.assertTrue(result["success"])
		self.assertIsNotNone(result["latest_check"])

	def test_api_run_check(self):
		"""Test API to create a new check."""
		from lifegence_business.credit.api.anti_social import run_anti_social_check

		result = run_anti_social_check(
			customer="_Test ASC Customer",
			check_source="帝国データバンク",
			result="問題なし",
		)
		self.assertTrue(result["success"])
		self.assertIn("check", result)
