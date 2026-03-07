# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestBudgetForecast(FrappeTestCase):
	"""Test cases for Budget Forecast DocType."""

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
			settings.forecast_method = "Linear"
			settings.max_revision_count = 3
			settings.save(ignore_permissions=True)
		frappe.db.commit()

	def _get_test_company(self):
		return frappe.db.get_value("Company", {}, "name") or "_Test Company"

	def _create_approved_plan(self):
		company = self._get_test_company()
		account = frappe.db.get_value("Account", {"company": company, "is_group": 0}, "name") or "Office Expenses - _TC"
		doc = frappe.get_doc({
			"doctype": "Budget Plan",
			"budget_title": "テスト着地見込み用予算",
			"fiscal_year": frappe.db.get_value("Fiscal Year", {"disabled": 0}, "name") or "2026",
			"company": company,
			"department": frappe.db.get_value("Department", {"company": company}, "name") or "",
			"cost_center": frappe.db.get_value("Cost Center", {"company": company, "is_group": 0}, "name") or f"{company} - _TC",
			"budget_type": "Expense",
			"status": "Approved",
			"items": [{"account": account, "month_1": 100000, "month_2": 100000, "month_3": 100000, "annual_total": 1200000}],
		})
		doc.insert(ignore_permissions=True)
		return doc

	def _create_forecast(self, budget_plan, **kwargs):
		account = frappe.db.get_value("Account", {"company": self._get_test_company(), "is_group": 0}, "name") or "Office Expenses - _TC"
		defaults = {
			"doctype": "Budget Forecast",
			"budget_plan": budget_plan,
			"forecast_month": 6,
			"forecast_method": "Linear",
			"forecast_items": [{
				"account": account,
				"budget_amount": 1200000,
				"actual_to_date": 500000,
			}],
		}
		defaults.update(kwargs)
		doc = frappe.get_doc(defaults)
		doc.insert(ignore_permissions=True)
		return doc

	def test_create_forecast(self):
		"""Test basic forecast creation."""
		bp = self._create_approved_plan()
		fc = self._create_forecast(bp.name)
		self.assertEqual(fc.forecast_method, "Linear")
		self.assertIsNotNone(fc.forecast_date)

	def test_linear_forecast_calculation(self):
		"""Test linear forecast method."""
		bp = self._create_approved_plan()
		fc = self._create_forecast(bp.name, forecast_method="Linear")
		fc.calculate_forecast()
		fc.save(ignore_permissions=True)
		item = fc.forecast_items[0]
		self.assertGreater(item.forecast_annual, 0)

	def test_average_forecast_calculation(self):
		"""Test average forecast method."""
		bp = self._create_approved_plan()
		fc = self._create_forecast(bp.name, forecast_method="Average")
		fc.calculate_forecast()
		fc.save(ignore_permissions=True)
		item = fc.forecast_items[0]
		self.assertGreater(item.forecast_annual, 0)

	def test_forecast_populates_from_plan(self):
		"""Test auto-population from budget plan."""
		bp = self._create_approved_plan()
		fc = self._create_forecast(bp.name)
		self.assertEqual(fc.fiscal_year, bp.fiscal_year)
		self.assertEqual(fc.company, bp.company)

	def test_forecast_variance_calculation(self):
		"""Test forecast variance calculation."""
		bp = self._create_approved_plan()
		fc = self._create_forecast(bp.name)
		fc.calculate_forecast()
		fc.save(ignore_permissions=True)
		item = fc.forecast_items[0]
		expected_variance = item.forecast_annual - item.budget_amount
		self.assertEqual(item.variance, expected_variance)

	def test_api_update_forecast(self):
		"""Test update_forecast API."""
		bp = self._create_approved_plan()
		fc = self._create_forecast(bp.name)
		from lifegence_business.budget.api.forecast import update_forecast

		result = update_forecast(
			budget_forecast=fc.name,
			budget_plan=bp.name,
			forecast_month=6,
			method="Average",
		)
		self.assertTrue(result["success"])
