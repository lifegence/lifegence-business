# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today, add_days


class TestAuditAPI(FrappeTestCase):
	"""Integration tests for Audit API endpoints."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		for role_name in ("Audit Manager", "Auditor", "Risk Manager"):
			if not frappe.db.exists("Role", role_name):
				frappe.get_doc({"doctype": "Role", "role_name": role_name, "desk_access": 1}).insert(ignore_permissions=True)
		settings = frappe.get_single("Audit Settings")
		if not settings.risk_review_cycle_days:
			settings.risk_matrix_enabled = 1
			settings.risk_matrix_size = "5x5"
			settings.risk_review_cycle_days = 90
			settings.auto_reminder_days = 7
			settings.overdue_check_frequency = "Daily"
			settings.save(ignore_permissions=True)
		frappe.db.commit()

	def _get_test_company(self):
		return frappe.db.get_value("Company", {}, "name") or "_Test Company"

	def _setup_test_data(self):
		company = self._get_test_company()
		plan = frappe.get_doc({
			"doctype": "Audit Plan",
			"plan_title": "API テスト監査計画",
			"fiscal_year": frappe.db.get_value("Fiscal Year", {"disabled": 0}, "name") or "2026",
			"company": company,
			"plan_period_start": today(),
			"plan_period_end": add_days(today(), 365),
			"audit_manager": frappe.session.user,
		})
		plan.insert(ignore_permissions=True)

		eng = frappe.get_doc({
			"doctype": "Audit Engagement",
			"engagement_title": "API テスト監査",
			"audit_plan": plan.name,
			"audit_type": "業務監査",
			"target_department": frappe.db.get_value("Department", {"company": company}, "name") or "",
			"period_start": today(),
			"period_end": add_days(today(), 90),
			"lead_auditor": frappe.session.user,
		})
		eng.insert(ignore_permissions=True)
		return plan, eng

	def test_audit_dashboard(self):
		"""Test get_audit_dashboard API."""
		self._setup_test_data()
		from lifegence_audit.api.audit import get_audit_dashboard

		result = get_audit_dashboard()
		self.assertTrue(result["success"])
		self.assertIn("plan_summary", result["data"])
		self.assertIn("findings_summary", result["data"])
		self.assertIn("risk_summary", result["data"])

	def test_create_finding_api(self):
		"""Test create_finding API."""
		_, eng = self._setup_test_data()
		from lifegence_audit.api.finding import create_finding

		result = create_finding(
			audit_engagement=eng.name,
			finding_title="API テスト発見事項",
			severity="High",
			category="業務プロセス",
			description="<p>API テスト</p>",
			recommendation="<p>テスト改善勧告</p>",
		)
		self.assertTrue(result["success"])
		self.assertIn("finding", result["data"])

	def test_get_findings_api(self):
		"""Test get_findings API."""
		from lifegence_audit.api.finding import get_findings

		result = get_findings()
		self.assertTrue(result["success"])
		self.assertIn("findings", result["data"])

	def test_risk_matrix_api(self):
		"""Test get_risk_matrix API."""
		company = self._get_test_company()
		frappe.get_doc({
			"doctype": "Risk Register",
			"risk_title": "API テストリスク",
			"risk_category": "ITリスク",
			"department": frappe.db.get_value("Department", {"company": company}, "name") or "",
			"risk_description": "<p>テスト</p>",
			"likelihood": "4",
			"impact": "4",
			"risk_owner": frappe.session.user,
		}).insert(ignore_permissions=True)

		from lifegence_audit.api.risk import get_risk_matrix

		result = get_risk_matrix()
		self.assertTrue(result["success"])
		self.assertIn("cells", result["data"])

	def test_risk_summary_api(self):
		"""Test get_risk_summary API."""
		from lifegence_audit.api.risk import get_risk_summary

		result = get_risk_summary()
		self.assertTrue(result["success"])
		self.assertIn("total_risks", result["data"])

	def test_overdue_actions_api(self):
		"""Test get_overdue_actions API."""
		from lifegence_audit.api.corrective_action import get_overdue_actions

		result = get_overdue_actions()
		self.assertTrue(result["success"])
		self.assertIn("overdue_actions", result["data"])
