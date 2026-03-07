# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today


class TestBudgetRevision(FrappeTestCase):
	"""Test cases for Budget Revision DocType."""

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
			"budget_title": "テスト修正用予算",
			"fiscal_year": frappe.db.get_value("Fiscal Year", {"disabled": 0}, "name") or "2026",
			"company": company,
			"department": frappe.db.get_value("Department", {"company": company}, "name") or "",
			"cost_center": frappe.db.get_value("Cost Center", {"company": company, "is_group": 0}, "name") or f"{company} - _TC",
			"budget_type": "Expense",
			"status": "Approved",
			"items": [{"account": account, "month_1": 500000, "annual_total": 500000}],
		})
		doc.insert(ignore_permissions=True)
		return doc

	def _create_revision(self, budget_plan, **kwargs):
		account = frappe.db.get_value("Account", {"company": self._get_test_company(), "is_group": 0}, "name") or "Office Expenses - _TC"
		defaults = {
			"doctype": "Budget Revision",
			"budget_plan": budget_plan,
			"revision_date": today(),
			"revision_type": "Increase",
			"reason": "テスト増額",
			"revised_items": [{
				"account": account,
				"original_annual_total": 500000,
				"revised_annual_total": 700000,
			}],
		}
		defaults.update(kwargs)
		doc = frappe.get_doc(defaults)
		doc.insert(ignore_permissions=True)
		return doc

	def test_create_revision(self):
		"""Test basic revision creation."""
		bp = self._create_approved_plan()
		rev = self._create_revision(bp.name)
		self.assertEqual(rev.status, "Draft")
		self.assertEqual(rev.revision_type, "Increase")

	def test_revision_totals(self):
		"""Test total calculations."""
		bp = self._create_approved_plan()
		rev = self._create_revision(bp.name)
		self.assertEqual(rev.total_change_amount, 200000)

	def test_revision_populates_from_plan(self):
		"""Test auto-population from budget plan."""
		bp = self._create_approved_plan()
		rev = self._create_revision(bp.name)
		self.assertEqual(rev.fiscal_year, bp.fiscal_year)

	def test_api_create_revision(self):
		"""Test create_revision API."""
		bp = self._create_approved_plan()
		from lifegence_budget.api.budget_plan import create_revision

		account = frappe.db.get_value("Account", {"company": self._get_test_company(), "is_group": 0}, "name") or "Office Expenses - _TC"
		result = create_revision(
			budget_plan=bp.name,
			reason="API増額テスト",
			revision_type="Increase",
			revised_items=[{"account": account, "original_annual_total": 500000, "revised_annual_total": 800000}],
		)
		self.assertTrue(result["success"])
		self.assertIn("revision", result["data"])
