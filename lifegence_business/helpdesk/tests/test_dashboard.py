# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestHDDashboard(FrappeTestCase):
	"""Test cases for helpdesk dashboard API."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls._ensure_roles()
		cls._ensure_sla_policy()
		cls._ensure_test_tickets()

	@classmethod
	def _ensure_roles(cls):
		for role_name in ("Support Manager", "Support Agent"):
			if not frappe.db.exists("Role", role_name):
				frappe.get_doc({
					"doctype": "Role",
					"role_name": role_name,
					"desk_access": 1,
				}).insert(ignore_permissions=True)

	@classmethod
	def _ensure_sla_policy(cls):
		if not frappe.db.exists("HD SLA Policy", "テストSLA"):
			frappe.get_doc({
				"doctype": "HD SLA Policy",
				"policy_name": "テストSLA",
				"is_default": 1,
				"enabled": 1,
				"low_response_time": 24,
				"low_resolution_time": 72,
				"medium_response_time": 8,
				"medium_resolution_time": 24,
				"high_response_time": 4,
				"high_resolution_time": 8,
				"urgent_response_time": 1,
				"urgent_resolution_time": 4,
			}).insert(ignore_permissions=True)
			frappe.db.commit()

	@classmethod
	def _ensure_test_tickets(cls):
		"""Create test tickets for dashboard testing."""
		# Create Open ticket
		if not frappe.db.exists("HD Ticket", {"subject": "ダッシュボードテスト_Open"}):
			frappe.get_doc({
				"doctype": "HD Ticket",
				"subject": "ダッシュボードテスト_Open",
				"description": "テスト",
				"raised_by_name": "テスト",
				"ticket_type": "社内",
				"priority": "Medium",
				"status": "Open",
			}).insert(ignore_permissions=True)

		# Create In Progress ticket
		if not frappe.db.exists("HD Ticket", {"subject": "ダッシュボードテスト_InProgress"}):
			doc = frappe.get_doc({
				"doctype": "HD Ticket",
				"subject": "ダッシュボードテスト_InProgress",
				"description": "テスト",
				"raised_by_name": "テスト",
				"ticket_type": "社内",
				"priority": "High",
				"status": "Open",
			})
			doc.insert(ignore_permissions=True)
			doc.status = "In Progress"
			doc.save(ignore_permissions=True)

		# Create Resolved ticket
		if not frappe.db.exists("HD Ticket", {"subject": "ダッシュボードテスト_Resolved"}):
			doc = frappe.get_doc({
				"doctype": "HD Ticket",
				"subject": "ダッシュボードテスト_Resolved",
				"description": "テスト",
				"raised_by_name": "テスト",
				"ticket_type": "社内",
				"priority": "Low",
				"status": "Open",
			})
			doc.insert(ignore_permissions=True)
			doc.status = "In Progress"
			doc.save(ignore_permissions=True)
			doc.status = "Resolved"
			doc.resolution = "解決済み"
			doc.save(ignore_permissions=True)

		frappe.db.commit()

	# ─── TC-DB01: Dashboard Counts ──────────────────────────────────

	def test_dashboard_counts(self):
		"""TC-DB01: Verify Open/In Progress/Resolved counts."""
		from lifegence_helpdesk.api.dashboard import get_helpdesk_dashboard

		result = get_helpdesk_dashboard()
		self.assertTrue(result["success"])

		counts = result["status_counts"]
		self.assertGreaterEqual(counts["Open"], 1)
		self.assertGreaterEqual(counts["In Progress"], 1)
		self.assertGreaterEqual(counts["Resolved"], 1)

	# ─── TC-DB02: SLA Compliance Rate ───────────────────────────────

	def test_sla_compliance_rate(self):
		"""TC-DB02: Verify SLA compliance rate calculation."""
		from lifegence_helpdesk.api.dashboard import get_helpdesk_dashboard

		result = get_helpdesk_dashboard()
		self.assertTrue(result["success"])

		sla = result["sla"]
		self.assertIn("compliance_rate", sla)
		self.assertGreaterEqual(sla["compliance_rate"], 0)
		self.assertLessEqual(sla["compliance_rate"], 100)
