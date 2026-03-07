# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestBudgetAPI(FrappeTestCase):
	"""Integration tests for Budget API endpoints."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		if not frappe.db.exists("Role", "Budget Manager"):
			frappe.get_doc({
				"doctype": "Role",
				"role_name": "Budget Manager",
				"desk_access": 1,
			}).insert(ignore_permissions=True)
		settings = frappe.get_single("Budget Settings")
		if not settings.fiscal_year_start_month:
			settings.fiscal_year_start_month = "4"
			settings.max_revision_count = 3
			settings.save(ignore_permissions=True)
		frappe.db.commit()

	def _get_test_company(self):
		return frappe.db.get_value("Company", {}, "name") or "_Test Company"

	def _create_plan(self):
		company = self._get_test_company()
		account = frappe.db.get_value("Account", {"company": company, "is_group": 0}, "name") or "Office Expenses - _TC"
		doc = frappe.get_doc({
			"doctype": "Budget Plan",
			"budget_title": "API テスト予算",
			"fiscal_year": frappe.db.get_value("Fiscal Year", {"disabled": 0}, "name") or "2026",
			"company": company,
			"department": frappe.db.get_value("Department", {"company": company}, "name") or "",
			"cost_center": frappe.db.get_value("Cost Center", {"company": company, "is_group": 0}, "name") or f"{company} - _TC",
			"budget_type": "Expense",
			"items": [{"account": account, "month_1": 100000, "annual_total": 1200000}],
		})
		doc.insert(ignore_permissions=True)
		return doc

	def test_get_budget_vs_actual(self):
		"""Test get_budget_vs_actual API."""
		bp = self._create_plan()
		bp.status = "Approved"
		bp.save(ignore_permissions=True)

		from lifegence_budget.api.budget_actual import get_budget_vs_actual

		result = get_budget_vs_actual(
			company=bp.company,
			fiscal_year=bp.fiscal_year,
		)
		self.assertTrue(result["success"])
		self.assertIn("summary", result["data"])

	def test_submit_budget_plan(self):
		"""Test submit_budget_plan API."""
		bp = self._create_plan()
		from lifegence_budget.api.budget_plan import submit_budget_plan

		result = submit_budget_plan(budget_plan=bp.name, action="submit")
		self.assertTrue(result["success"])
		self.assertEqual(result["data"]["new_status"], "Submitted")

	def test_create_revision_api(self):
		"""Test create_revision API."""
		bp = self._create_plan()
		bp.status = "Approved"
		bp.save(ignore_permissions=True)

		account = frappe.db.get_value("Account", {"company": self._get_test_company(), "is_group": 0}, "name") or "Office Expenses - _TC"
		from lifegence_budget.api.budget_plan import create_revision

		result = create_revision(
			budget_plan=bp.name,
			reason="API統合テスト増額",
			revision_type="Increase",
			revised_items=[{"account": account, "original_annual_total": 1200000, "revised_annual_total": 1500000}],
		)
		self.assertTrue(result["success"])

	def test_update_forecast_api(self):
		"""Test update_forecast API."""
		bp = self._create_plan()
		bp.status = "Approved"
		bp.save(ignore_permissions=True)

		account = frappe.db.get_value("Account", {"company": self._get_test_company(), "is_group": 0}, "name") or "Office Expenses - _TC"
		fc = frappe.get_doc({
			"doctype": "Budget Forecast",
			"budget_plan": bp.name,
			"forecast_month": 6,
			"forecast_method": "Linear",
			"forecast_items": [{"account": account, "budget_amount": 1200000, "actual_to_date": 600000}],
		})
		fc.insert(ignore_permissions=True)

		from lifegence_budget.api.forecast import update_forecast

		result = update_forecast(
			budget_forecast=fc.name,
			budget_plan=bp.name,
			forecast_month=6,
			method="Average",
		)
		self.assertTrue(result["success"])
