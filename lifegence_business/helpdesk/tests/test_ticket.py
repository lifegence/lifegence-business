# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestHDTicket(FrappeTestCase):
	"""Test cases for HD Ticket DocType and ticket API."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls._ensure_roles()
		cls._ensure_category()
		cls._ensure_sla_policy()
		cls._ensure_company()
		cls._ensure_employee()

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
	def _ensure_category(cls):
		if frappe.db.exists("HD Category", "IT"):
			# Ensure default_assigned_to is set for auto-assignment test
			frappe.db.set_value(
				"HD Category", "IT", "default_assigned_to", "Administrator"
			)
		else:
			frappe.get_doc({
				"doctype": "HD Category",
				"category_name": "IT",
				"description": "IT関連の問い合わせ",
				"default_priority": "High",
				"default_assigned_to": "Administrator",
				"is_external": 0,
				"enabled": 1,
			}).insert(ignore_permissions=True)
		if not frappe.db.exists("HD Category", "顧客サポート"):
			frappe.get_doc({
				"doctype": "HD Category",
				"category_name": "顧客サポート",
				"description": "顧客からの問い合わせ",
				"is_external": 1,
				"enabled": 1,
			}).insert(ignore_permissions=True)
		frappe.db.commit()

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

	@classmethod
	def _ensure_company(cls):
		if not frappe.db.exists("Company", "テスト株式会社"):
			frappe.get_doc({
				"doctype": "Company",
				"company_name": "テスト株式会社",
				"abbr": "TST",
				"country": "Japan",
				"default_currency": "JPY",
			}).insert(ignore_permissions=True)

	@classmethod
	def _ensure_employee(cls):
		if not frappe.db.exists("Employee", {"employee_name": "テスト太郎"}):
			emp = frappe.get_doc({
				"doctype": "Employee",
				"employee_name": "テスト太郎",
				"first_name": "太郎",
				"company": "テスト株式会社",
				"status": "Active",
				"gender": "Male",
				"date_of_birth": "1990-01-01",
				"date_of_joining": "2020-04-01",
			})
			emp.insert(ignore_permissions=True)
			cls.test_employee = emp.name
		else:
			cls.test_employee = frappe.db.get_value(
				"Employee", {"employee_name": "テスト太郎"}, "name"
			)
		frappe.db.commit()

	def _create_ticket(self, **kwargs):
		"""Helper to create a test ticket."""
		defaults = {
			"doctype": "HD Ticket",
			"subject": "テストチケット",
			"description": "テストの問い合わせ内容です。",
			"raised_by_name": "テスト太郎",
			"raised_by_email": "test@example.com",
			"ticket_type": "社内",
			"priority": "Medium",
		}
		defaults.update(kwargs)
		doc = frappe.get_doc(defaults)
		doc.insert(ignore_permissions=True)
		return doc

	# ─── TC-TK01: Create Ticket ─────────────────────────────────────

	def test_create_ticket(self):
		"""TC-TK01: Create a ticket with naming series HD-."""
		ticket = self._create_ticket()
		self.assertTrue(ticket.name.startswith("HD-"))
		self.assertEqual(ticket.status, "Open")
		self.assertEqual(ticket.priority, "Medium")

	# ─── TC-TK02: Auto Assignment ───────────────────────────────────

	def test_ticket_auto_assignment(self):
		"""TC-TK02: Category default_assigned_to auto-assigns."""
		ticket = self._create_ticket(category="IT")
		self.assertEqual(ticket.assigned_to, "Administrator")

	# ─── TC-TK03: Status Transitions ────────────────────────────────

	def test_status_transitions(self):
		"""TC-TK03: Open → In Progress → Resolved → Closed."""
		ticket = self._create_ticket()

		ticket.status = "In Progress"
		ticket.save(ignore_permissions=True)
		self.assertEqual(ticket.status, "In Progress")

		ticket.status = "Resolved"
		ticket.resolution = "問題を修正しました。"
		ticket.save(ignore_permissions=True)
		self.assertEqual(ticket.status, "Resolved")

		ticket.status = "Closed"
		ticket.save(ignore_permissions=True)
		self.assertEqual(ticket.status, "Closed")

	# ─── TC-TK04: Invalid Status Transition ─────────────────────────

	def test_invalid_status_transition(self):
		"""TC-TK04: Closed → Open should be rejected."""
		ticket = self._create_ticket()
		ticket.status = "In Progress"
		ticket.save(ignore_permissions=True)
		ticket.status = "Resolved"
		ticket.save(ignore_permissions=True)
		ticket.status = "Closed"
		ticket.save(ignore_permissions=True)

		ticket.status = "Open"
		self.assertRaises(frappe.ValidationError, ticket.save, ignore_permissions=True)

	# ─── TC-TK05: Add External Comment ──────────────────────────────

	def test_add_comment_external(self):
		"""TC-TK05: Add an external comment."""
		ticket = self._create_ticket()
		ticket.append("comments", {
			"comment": "外部向けコメント",
			"commented_by": frappe.session.user,
			"commented_on": frappe.utils.now_datetime(),
			"is_internal": 0,
		})
		ticket.save(ignore_permissions=True)

		self.assertEqual(len(ticket.comments), 1)
		self.assertEqual(ticket.comments[0].is_internal, 0)

	# ─── TC-TK06: Add Internal Comment ──────────────────────────────

	def test_add_comment_internal(self):
		"""TC-TK06: Add an internal comment (is_internal=1)."""
		ticket = self._create_ticket()
		ticket.append("comments", {
			"comment": "内部メモ: 調査中",
			"commented_by": frappe.session.user,
			"commented_on": frappe.utils.now_datetime(),
			"is_internal": 1,
		})
		ticket.save(ignore_permissions=True)

		self.assertEqual(len(ticket.comments), 1)
		self.assertEqual(ticket.comments[0].is_internal, 1)

	# ─── TC-TK07: Internal Ticket with Employee ─────────────────────

	def test_ticket_type_internal(self):
		"""TC-TK07: Internal ticket links to employee."""
		ticket = self._create_ticket(
			ticket_type="社内",
			raised_by_employee=self.test_employee,
			company="テスト株式会社",
		)
		self.assertEqual(ticket.ticket_type, "社内")
		self.assertEqual(ticket.raised_by_employee, self.test_employee)

	# ─── TC-TK08: External Ticket ───────────────────────────────────

	def test_ticket_type_external(self):
		"""TC-TK08: External ticket with email."""
		ticket = self._create_ticket(
			ticket_type="社外",
			raised_by_name="外部顧客",
			raised_by_email="customer@example.com",
			category="顧客サポート",
		)
		self.assertEqual(ticket.ticket_type, "社外")
		self.assertEqual(ticket.raised_by_email, "customer@example.com")

	# ─── TC-TK09: Satisfaction Rating ───────────────────────────────

	def test_satisfaction_rating(self):
		"""TC-TK09: Add satisfaction rating after resolution."""
		ticket = self._create_ticket()
		ticket.status = "In Progress"
		ticket.save(ignore_permissions=True)
		ticket.status = "Resolved"
		ticket.resolution = "修正済み"
		ticket.save(ignore_permissions=True)

		ticket.satisfaction_rating = "5"
		ticket.satisfaction_feedback = "迅速な対応ありがとうございます。"
		ticket.save(ignore_permissions=True)

		self.assertEqual(ticket.satisfaction_rating, "5")

	# ─── TC-TK10: Create Ticket via API ─────────────────────────────

	def test_create_ticket_api(self):
		"""TC-TK10: Create a ticket via the API function."""
		from lifegence_business.helpdesk.api.ticket import create_ticket

		result = create_ticket(
			subject="API経由チケット",
			description="APIからの問い合わせ",
			category="IT",
			priority="High",
		)

		self.assertTrue(result["success"])
		self.assertTrue(result["ticket"].startswith("HD-"))
		self.assertEqual(result["status"], "Open")
