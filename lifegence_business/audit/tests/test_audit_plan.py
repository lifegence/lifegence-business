# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today, add_days


class TestAuditPlan(FrappeTestCase):
	"""Test cases for Audit Plan DocType."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls._ensure_roles()

	@classmethod
	def _ensure_roles(cls):
		for role_name in ("Audit Manager", "Auditor", "Risk Manager"):
			if not frappe.db.exists("Role", role_name):
				frappe.get_doc({
					"doctype": "Role",
					"role_name": role_name,
					"desk_access": 1,
				}).insert(ignore_permissions=True)
		frappe.db.commit()

	def _get_test_company(self):
		return frappe.db.get_value("Company", {}, "name") or "_Test Company"

	def _create_plan(self, **kwargs):
		company = self._get_test_company()
		defaults = {
			"doctype": "Audit Plan",
			"plan_title": "テスト監査計画",
			"fiscal_year": frappe.db.get_value("Fiscal Year", {"disabled": 0}, "name") or "2026",
			"company": company,
			"plan_period_start": today(),
			"plan_period_end": add_days(today(), 365),
			"audit_manager": frappe.session.user,
		}
		defaults.update(kwargs)
		doc = frappe.get_doc(defaults)
		doc.insert(ignore_permissions=True)
		return doc

	def test_create_plan(self):
		"""Test basic audit plan creation."""
		doc = self._create_plan()
		self.assertEqual(doc.status, "Draft")
		self.assertIsNotNone(doc.audit_manager)

	def test_status_transition_submitted(self):
		"""Test Draft -> Submitted transition."""
		doc = self._create_plan()
		doc.status = "Submitted"
		doc.save(ignore_permissions=True)
		self.assertEqual(doc.status, "Submitted")

	def test_status_transition_approved(self):
		"""Test Submitted -> Approved transition."""
		doc = self._create_plan()
		doc.status = "Submitted"
		doc.save(ignore_permissions=True)

		doc.status = "Approved"
		doc.save(ignore_permissions=True)
		self.assertEqual(doc.status, "Approved")
		self.assertIsNotNone(doc.approved_by)
		self.assertIsNotNone(doc.approval_date)

	def test_invalid_status_transition(self):
		"""Test that invalid status transitions are blocked."""
		doc = self._create_plan()
		doc.status = "Approved"
		self.assertRaises(frappe.ValidationError, doc.save)

	def test_date_validation(self):
		"""Test that start date cannot be after end date."""
		self.assertRaises(
			frappe.ValidationError,
			self._create_plan,
			plan_period_start=add_days(today(), 365),
			plan_period_end=today(),
		)
