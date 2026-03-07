# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestBudgetPlan(FrappeTestCase):
	"""Test cases for Budget Plan DocType."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls._ensure_roles()
		cls._ensure_settings()

	@classmethod
	def _ensure_roles(cls):
		if not frappe.db.exists("Role", "Budget Manager"):
			frappe.get_doc({
				"doctype": "Role",
				"role_name": "Budget Manager",
				"desk_access": 1,
			}).insert(ignore_permissions=True)

	@classmethod
	def _ensure_settings(cls):
		settings = frappe.get_single("Budget Settings")
		if not settings.fiscal_year_start_month:
			settings.fiscal_year_start_month = "4"
			settings.budget_currency = "JPY"
			settings.amount_rounding = "千円"
			settings.variance_threshold_pct = 10
			settings.variance_action = "Warn"
			settings.forecast_method = "Linear"
			settings.max_revision_count = 3
			settings.save(ignore_permissions=True)
		frappe.db.commit()

	def _get_test_company(self):
		return frappe.db.get_value("Company", {}, "name") or "_Test Company"

	def _get_test_fiscal_year(self):
		return frappe.db.get_value("Fiscal Year", {"disabled": 0}, "name") or "2026"

	def _get_test_cost_center(self):
		company = self._get_test_company()
		return frappe.db.get_value("Cost Center", {"company": company, "is_group": 0}, "name") or f"{company} - _TC"

	def _get_test_account(self):
		company = self._get_test_company()
		return frappe.db.get_value("Account", {"company": company, "is_group": 0}, "name") or "Office Expenses - _TC"

	def _create_plan(self, **kwargs):
		company = self._get_test_company()
		defaults = {
			"doctype": "Budget Plan",
			"budget_title": "テスト予算計画",
			"fiscal_year": self._get_test_fiscal_year(),
			"company": company,
			"department": frappe.db.get_value("Department", {"company": company}, "name") or "",
			"cost_center": self._get_test_cost_center(),
			"budget_type": "Expense",
			"items": [{
				"account": self._get_test_account(),
				"month_1": 100000,
				"month_2": 100000,
				"month_3": 100000,
				"month_4": 100000,
				"month_5": 100000,
				"month_6": 100000,
				"month_7": 100000,
				"month_8": 100000,
				"month_9": 100000,
				"month_10": 100000,
				"month_11": 100000,
				"month_12": 100000,
			}],
		}
		defaults.update(kwargs)
		doc = frappe.get_doc(defaults)
		doc.insert(ignore_permissions=True)
		return doc

	def test_create_plan(self):
		"""Test basic budget plan creation."""
		doc = self._create_plan()
		self.assertEqual(doc.status, "Draft")
		self.assertEqual(doc.budget_type, "Expense")
		self.assertIsNotNone(doc.prepared_by)

	def test_annual_total_calculation(self):
		"""Test auto-calculation of annual total."""
		doc = self._create_plan()
		self.assertEqual(doc.total_annual_amount, 1200000)

	def test_equal_distribution(self):
		"""Test equal distribution of budget items."""
		doc = self._create_plan(items=[{
			"account": self._get_test_account(),
			"annual_total": 1200000,
			"distribution_method": "Equal",
		}])
		item = doc.items[0]
		self.assertEqual(item.month_1, 100000)

	def test_status_transition_to_approved(self):
		"""Test status transition Draft -> Submitted -> Approved."""
		doc = self._create_plan()
		doc.status = "Submitted"
		doc.save(ignore_permissions=True)
		self.assertEqual(doc.status, "Submitted")

		doc.status = "Approved"
		doc.save(ignore_permissions=True)
		self.assertEqual(doc.status, "Approved")
		self.assertIsNotNone(doc.approved_by)
		self.assertIsNotNone(doc.approved_date)

	def test_rejection_requires_reason(self):
		"""Test that rejection requires a reason."""
		doc = self._create_plan()
		doc.status = "Submitted"
		doc.save(ignore_permissions=True)

		doc.status = "Rejected"
		doc.rejection_reason = ""
		self.assertRaises(frappe.ValidationError, doc.save)

	def test_invalid_status_transition(self):
		"""Test that invalid status transitions are blocked."""
		doc = self._create_plan()
		doc.status = "Approved"
		self.assertRaises(frappe.ValidationError, doc.save)

	def test_api_submit_plan(self):
		"""Test submit_budget_plan API."""
		doc = self._create_plan()
		from lifegence_business.budget.api.budget_plan import submit_budget_plan

		result = submit_budget_plan(budget_plan=doc.name, action="submit")
		self.assertTrue(result["success"])
		self.assertEqual(result["data"]["new_status"], "Submitted")
