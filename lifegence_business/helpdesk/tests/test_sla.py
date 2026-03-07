# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import now_datetime, add_to_date


class TestHDSLA(FrappeTestCase):
	"""Test cases for SLA policy and SLA tracking."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls._ensure_roles()
		cls._ensure_sla_policy()

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
				"business_hours_start": "09:00:00",
				"business_hours_end": "18:00:00",
			}).insert(ignore_permissions=True)
			frappe.db.commit()

	def _create_ticket(self, **kwargs):
		defaults = {
			"doctype": "HD Ticket",
			"subject": "SLAテスト",
			"description": "SLAテスト内容",
			"raised_by_name": "テスト太郎",
			"ticket_type": "社内",
			"priority": "Medium",
		}
		defaults.update(kwargs)
		doc = frappe.get_doc(defaults)
		doc.insert(ignore_permissions=True)
		return doc

	# ─── TC-SLA01: SLA Auto Apply ───────────────────────────────────

	def test_sla_auto_apply(self):
		"""TC-SLA01: SLA policy is auto-applied on ticket creation."""
		ticket = self._create_ticket()
		self.assertEqual(ticket.sla_policy, "テストSLA")
		self.assertIsNotNone(ticket.response_due)
		self.assertIsNotNone(ticket.resolution_due)

	# ─── TC-SLA02: Response Due Calculation ─────────────────────────

	def test_response_due_calculation(self):
		"""TC-SLA02: Response due is calculated based on priority."""
		# High priority: 4h response time
		ticket = self._create_ticket(priority="High")
		response_due = frappe.utils.get_datetime(ticket.response_due)
		creation = frappe.utils.get_datetime(ticket.creation)
		diff_hours = (response_due - creation).total_seconds() / 3600
		self.assertAlmostEqual(diff_hours, 4, delta=0.1)

	# ─── TC-SLA03: Resolution Due Calculation ───────────────────────

	def test_resolution_due_calculation(self):
		"""TC-SLA03: Resolution due is calculated based on priority."""
		# Urgent priority: 4h resolution time
		ticket = self._create_ticket(priority="Urgent")
		resolution_due = frappe.utils.get_datetime(ticket.resolution_due)
		creation = frappe.utils.get_datetime(ticket.creation)
		diff_hours = (resolution_due - creation).total_seconds() / 3600
		self.assertAlmostEqual(diff_hours, 4, delta=0.1)

	# ─── TC-SLA04: SLA Pause on Waiting ─────────────────────────────

	def test_sla_pause_on_waiting(self):
		"""TC-SLA04: SLA timer pauses when status changes to Waiting for Customer."""
		ticket = self._create_ticket()
		ticket.status = "In Progress"
		ticket.save(ignore_permissions=True)

		ticket.status = "Waiting for Customer"
		ticket.save(ignore_permissions=True)

		# Check that a Paused timer event was added
		pause_events = [t for t in ticket.sla_timers if t.event == "Paused"]
		self.assertTrue(len(pause_events) > 0)

	# ─── TC-SLA05: SLA Breach Detection ─────────────────────────────

	def test_sla_breach_detection(self):
		"""TC-SLA05: SLA breach detected when past due."""
		ticket = self._create_ticket(priority="Urgent")

		# Manually set response_due to past
		past_time = add_to_date(now_datetime(), hours=-2)
		frappe.db.set_value("HD Ticket", ticket.name, "response_due", past_time)

		# Reload and save to trigger SLA check
		ticket.reload()
		ticket.status = "In Progress"
		ticket.save(ignore_permissions=True)

		# first_responded_on will be set, so check resolution_due breach instead
		# Set resolution_due to past too
		frappe.db.set_value("HD Ticket", ticket.name, "resolution_due", past_time)
		ticket.reload()
		ticket._update_sla_status()

		self.assertEqual(ticket.sla_status, "Breached")

	# ─── TC-SLA06: SLA Warning Threshold ────────────────────────────

	def test_sla_warning_threshold(self):
		"""TC-SLA06: Warning at 80% of SLA time elapsed."""
		ticket = self._create_ticket(priority="Low")

		# Low: 72h resolution. Set creation to 60h ago so >80% elapsed
		past_creation = add_to_date(now_datetime(), hours=-60)
		resolution_due = add_to_date(past_creation, hours=72)  # 12h from now
		frappe.db.set_value("HD Ticket", ticket.name, {
			"creation": past_creation,
			"resolution_due": resolution_due,
		})

		ticket.reload()
		ticket.first_responded_on = past_creation  # Already responded
		ticket._update_sla_status()

		self.assertEqual(ticket.sla_status, "Warning")
