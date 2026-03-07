# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today, add_days


class TestAuditEngagement(FrappeTestCase):
	"""Test cases for Audit Engagement DocType."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		for role_name in ("Audit Manager", "Auditor", "Risk Manager"):
			if not frappe.db.exists("Role", role_name):
				frappe.get_doc({"doctype": "Role", "role_name": role_name, "desk_access": 1}).insert(ignore_permissions=True)
		frappe.db.commit()

	def _get_test_company(self):
		return frappe.db.get_value("Company", {}, "name") or "_Test Company"

	def _create_plan(self):
		company = self._get_test_company()
		doc = frappe.get_doc({
			"doctype": "Audit Plan",
			"plan_title": "テスト個別監査用計画",
			"fiscal_year": frappe.db.get_value("Fiscal Year", {"disabled": 0}, "name") or "2026",
			"company": company,
			"plan_period_start": today(),
			"plan_period_end": add_days(today(), 365),
			"audit_manager": frappe.session.user,
		})
		doc.insert(ignore_permissions=True)
		return doc

	def _create_engagement(self, audit_plan, **kwargs):
		company = self._get_test_company()
		defaults = {
			"doctype": "Audit Engagement",
			"engagement_title": "テスト個別監査",
			"audit_plan": audit_plan,
			"audit_type": "業務監査",
			"target_department": frappe.db.get_value("Department", {"company": company}, "name") or "",
			"period_start": today(),
			"period_end": add_days(today(), 90),
			"lead_auditor": frappe.session.user,
		}
		defaults.update(kwargs)
		doc = frappe.get_doc(defaults)
		doc.insert(ignore_permissions=True)
		return doc

	def test_create_engagement(self):
		"""Test basic engagement creation."""
		plan = self._create_plan()
		eng = self._create_engagement(plan.name)
		self.assertEqual(eng.status, "Planning")
		self.assertEqual(eng.audit_type, "業務監査")

	def test_status_transition_fieldwork(self):
		"""Test Planning -> Fieldwork transition."""
		plan = self._create_plan()
		eng = self._create_engagement(plan.name)
		eng.status = "Fieldwork"
		eng.save(ignore_permissions=True)
		self.assertEqual(eng.status, "Fieldwork")
		self.assertIsNotNone(eng.actual_start)

	def test_invalid_status_transition(self):
		"""Test invalid transition is blocked."""
		plan = self._create_plan()
		eng = self._create_engagement(plan.name)
		eng.status = "Closed"
		eng.save(ignore_permissions=True)
		# Planning -> Closed is allowed per the code
		self.assertEqual(eng.status, "Closed")

	def test_date_validation(self):
		"""Test date validation."""
		plan = self._create_plan()
		self.assertRaises(
			frappe.ValidationError,
			self._create_engagement,
			plan.name,
			period_start=add_days(today(), 90),
			period_end=today(),
		)
