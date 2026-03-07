# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today, add_days


class TestAuditFinding(FrappeTestCase):
	"""Test cases for Audit Finding DocType."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		for role_name in ("Audit Manager", "Auditor", "Risk Manager"):
			if not frappe.db.exists("Role", role_name):
				frappe.get_doc({"doctype": "Role", "role_name": role_name, "desk_access": 1}).insert(ignore_permissions=True)
		frappe.db.commit()

	def _get_test_company(self):
		return frappe.db.get_value("Company", {}, "name") or "_Test Company"

	def _create_engagement(self):
		company = self._get_test_company()
		plan = frappe.get_doc({
			"doctype": "Audit Plan",
			"plan_title": "テスト発見事項用計画",
			"fiscal_year": frappe.db.get_value("Fiscal Year", {"disabled": 0}, "name") or "2026",
			"company": company,
			"plan_period_start": today(),
			"plan_period_end": add_days(today(), 365),
			"audit_manager": frappe.session.user,
		})
		plan.insert(ignore_permissions=True)

		eng = frappe.get_doc({
			"doctype": "Audit Engagement",
			"engagement_title": "テスト発見事項用監査",
			"audit_plan": plan.name,
			"audit_type": "業務監査",
			"target_department": frappe.db.get_value("Department", {"company": company}, "name") or "",
			"period_start": today(),
			"period_end": add_days(today(), 90),
			"lead_auditor": frappe.session.user,
		})
		eng.insert(ignore_permissions=True)
		return eng

	def _create_finding(self, engagement, **kwargs):
		defaults = {
			"doctype": "Audit Finding",
			"finding_title": "テスト発見事項",
			"audit_engagement": engagement,
			"severity": "Medium",
			"category": "業務プロセス",
			"description": "<p>テスト用発見事項です</p>",
			"recommendation": "<p>テスト改善勧告</p>",
		}
		defaults.update(kwargs)
		doc = frappe.get_doc(defaults)
		doc.insert(ignore_permissions=True)
		return doc

	def test_create_finding(self):
		"""Test basic finding creation."""
		eng = self._create_engagement()
		finding = self._create_finding(eng.name)
		self.assertEqual(finding.status, "Open")
		self.assertEqual(finding.severity, "Medium")
		self.assertIsNotNone(finding.reported_by)

	def test_finding_severity_levels(self):
		"""Test all severity levels."""
		eng = self._create_engagement()
		for severity in ["Critical", "High", "Medium", "Low", "Info"]:
			finding = self._create_finding(eng.name, severity=severity, finding_title=f"テスト {severity}")
			self.assertEqual(finding.severity, severity)

	def test_finding_close(self):
		"""Test closing a finding."""
		eng = self._create_engagement()
		finding = self._create_finding(eng.name)
		finding.status = "Closed"
		finding.save(ignore_permissions=True)
		self.assertEqual(finding.status, "Closed")
		self.assertIsNotNone(finding.closed_date)
		self.assertIsNotNone(finding.closed_by)

	def test_jsox_finding(self):
		"""Test J-SOX relevant finding."""
		eng = self._create_engagement()
		finding = self._create_finding(
			eng.name,
			jsox_relevant=1,
			jsox_deficiency_type="Material Weakness",
		)
		self.assertEqual(finding.jsox_relevant, 1)
		self.assertEqual(finding.jsox_deficiency_type, "Material Weakness")
