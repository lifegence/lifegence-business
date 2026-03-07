# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today, add_days


class TestCorrectiveAction(FrappeTestCase):
	"""Test cases for Corrective Action DocType."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		for role_name in ("Audit Manager", "Auditor", "Risk Manager"):
			if not frappe.db.exists("Role", role_name):
				frappe.get_doc({"doctype": "Role", "role_name": role_name, "desk_access": 1}).insert(ignore_permissions=True)
		frappe.db.commit()

	def _get_test_company(self):
		return frappe.db.get_value("Company", {}, "name") or "_Test Company"

	def _create_finding(self):
		company = self._get_test_company()
		plan = frappe.get_doc({
			"doctype": "Audit Plan",
			"plan_title": "テスト是正措置用計画",
			"fiscal_year": frappe.db.get_value("Fiscal Year", {"disabled": 0}, "name") or "2026",
			"company": company,
			"plan_period_start": today(),
			"plan_period_end": add_days(today(), 365),
			"audit_manager": frappe.session.user,
		})
		plan.insert(ignore_permissions=True)

		eng = frappe.get_doc({
			"doctype": "Audit Engagement",
			"engagement_title": "テスト是正措置用監査",
			"audit_plan": plan.name,
			"audit_type": "業務監査",
			"target_department": frappe.db.get_value("Department", {"company": company}, "name") or "",
			"period_start": today(),
			"period_end": add_days(today(), 90),
			"lead_auditor": frappe.session.user,
		})
		eng.insert(ignore_permissions=True)

		finding = frappe.get_doc({
			"doctype": "Audit Finding",
			"finding_title": "テスト是正措置用発見事項",
			"audit_engagement": eng.name,
			"severity": "High",
			"category": "業務プロセス",
			"description": "<p>テスト</p>",
			"recommendation": "<p>テスト勧告</p>",
		})
		finding.insert(ignore_permissions=True)
		return finding

	def _create_action(self, finding, **kwargs):
		defaults = {
			"doctype": "Corrective Action",
			"action_title": "テスト是正措置",
			"audit_finding": finding,
			"action_type": "Corrective",
			"action_description": "<p>テスト措置内容</p>",
			"responsible_person": frappe.session.user,
			"due_date": add_days(today(), 30),
			"priority": "Normal",
		}
		defaults.update(kwargs)
		doc = frappe.get_doc(defaults)
		doc.insert(ignore_permissions=True)
		return doc

	def test_create_action(self):
		"""Test basic corrective action creation."""
		finding = self._create_finding()
		action = self._create_action(finding.name)
		self.assertEqual(action.status, "Open")
		self.assertEqual(action.action_type, "Corrective")

	def test_complete_action(self):
		"""Test completing a corrective action."""
		finding = self._create_finding()
		action = self._create_action(finding.name)
		action.status = "Completed"
		action.save(ignore_permissions=True)
		self.assertEqual(action.status, "Completed")
		self.assertIsNotNone(action.completion_date)

	def test_overdue_check(self):
		"""Test overdue detection for past-due actions."""
		finding = self._create_finding()
		action = self._create_action(finding.name, due_date=add_days(today(), -5))
		self.assertEqual(action.status, "Open")

		from lifegence_audit.services.corrective_action_service import check_overdue_actions
		check_overdue_actions()

		action.reload()
		self.assertEqual(action.status, "Overdue")

	def test_action_updates_finding(self):
		"""Test that completing action updates finding status."""
		finding = self._create_finding()
		action = self._create_action(finding.name)

		action.status = "Completed"
		action.save(ignore_permissions=True)

		finding.reload()
		self.assertEqual(finding.status, "Remediated")

	def test_api_create_action(self):
		"""Test create_corrective_action API."""
		finding = self._create_finding()
		from lifegence_audit.api.corrective_action import create_corrective_action

		result = create_corrective_action(
			audit_finding=finding.name,
			action_title="APIテスト是正措置",
			action_description="<p>API経由</p>",
			responsible_person=frappe.session.user,
			due_date=str(add_days(today(), 30)),
			priority="High",
		)
		self.assertTrue(result["success"])
