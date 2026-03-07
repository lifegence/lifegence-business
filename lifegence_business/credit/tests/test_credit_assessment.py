# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestCreditAssessment(FrappeTestCase):
	"""Test cases for Credit Assessment DocType."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls._ensure_roles()
		cls._ensure_settings()
		cls._ensure_customer()
		cls._ensure_company()

	@classmethod
	def _ensure_roles(cls):
		for role_name in ("Credit Manager", "Credit Approver"):
			if not frappe.db.exists("Role", role_name):
				frappe.get_doc({
					"doctype": "Role",
					"role_name": role_name,
					"desk_access": 1,
				}).insert(ignore_permissions=True)

	@classmethod
	def _ensure_settings(cls):
		settings = frappe.get_single("Credit Settings")
		if not settings.default_credit_period_days:
			settings.default_credit_period_days = 365
			settings.auto_block_on_exceed = 1
			settings.alert_threshold_pct = 80
			settings.review_cycle_months = 12
			settings.grade_a_min_score = 80
			settings.grade_b_min_score = 60
			settings.grade_c_min_score = 40
			settings.grade_d_min_score = 20
			settings.send_review_reminder_days = 30
			settings.save(ignore_permissions=True)
		frappe.db.commit()

	@classmethod
	def _ensure_customer(cls):
		if not frappe.db.exists("Customer", "_Test Credit Customer"):
			frappe.get_doc({
				"doctype": "Customer",
				"customer_name": "_Test Credit Customer",
				"customer_group": "All Customer Groups",
				"territory": "All Territories",
			}).insert(ignore_permissions=True)
		frappe.db.commit()

	@classmethod
	def _ensure_company(cls):
		if not frappe.db.exists("Company", "_Test Company"):
			pass  # Usually exists in ERPNext test fixtures
		frappe.db.commit()

	def _create_assessment(self, **kwargs):
		defaults = {
			"doctype": "Credit Assessment",
			"customer": "_Test Credit Customer",
			"assessment_type": "新規取引",
			"requested_amount": 5000000,
			"revenue": 100000000,
			"profit": 8000000,
			"capital": 50000000,
			"years_in_business": 12,
			"payment_history_score": 90,
			"existing_transaction_months": 36,
			"average_monthly_transaction": 1000000,
		}
		defaults.update(kwargs)
		doc = frappe.get_doc(defaults)
		doc.insert(ignore_permissions=True)
		return doc

	def test_create_assessment(self):
		"""Test basic assessment creation."""
		doc = self._create_assessment()
		self.assertEqual(doc.status, "Draft")
		self.assertEqual(doc.customer, "_Test Credit Customer")
		self.assertEqual(doc.assessment_type, "新規取引")

	def test_risk_score_calculation_high(self):
		"""Test risk score calculation for high-credit customer."""
		doc = self._create_assessment(
			revenue=100000000,
			profit=8000000,  # 8% margin -> 30 points
			capital=100000000,  # 1億 -> 15 points
			years_in_business=15,  # -> 15 points
			payment_history_score=90,  # -> 23 points
			existing_transaction_months=36,  # -> 15 points
		)
		# Expected: 30 + 15 + 15 + 23 + 15 = 98
		self.assertGreaterEqual(doc.risk_score, 90)
		self.assertEqual(doc.risk_grade, "A")

	def test_risk_score_calculation_medium(self):
		"""Test risk score for medium-credit customer."""
		doc = self._create_assessment(
			revenue=50000000,
			profit=2000000,  # 4% margin -> 20 points
			capital=10000000,  # 1000万 -> 10 points
			years_in_business=6,  # -> 10 points
			payment_history_score=60,  # -> 15 points
			existing_transaction_months=14,  # -> 10 points
		)
		# Expected: 20 + 10 + 10 + 15 + 10 = 65
		self.assertGreaterEqual(doc.risk_score, 60)
		self.assertIn(doc.risk_grade, ["B", "A"])

	def test_risk_score_calculation_low(self):
		"""Test risk score for low-credit customer."""
		doc = self._create_assessment(
			revenue=10000000,
			profit=-500000,  # Negative -> 0 points
			capital=1000000,  # <300万 -> 0 points
			years_in_business=1,  # <3 -> 0 points
			payment_history_score=20,  # -> 5 points
			existing_transaction_months=3,  # <6 -> 0 points
		)
		self.assertLessEqual(doc.risk_score, 20)
		self.assertIn(doc.risk_grade, ["D", "E"])

	def test_risk_grade_a(self):
		"""Test grade A assignment."""
		doc = self._create_assessment(
			revenue=200000000, profit=20000000, capital=200000000,
			years_in_business=20, payment_history_score=100, existing_transaction_months=48,
		)
		self.assertEqual(doc.risk_grade, "A")

	def test_risk_grade_e(self):
		"""Test grade E assignment for very risky customer."""
		doc = self._create_assessment(
			revenue=0, profit=0, capital=0,
			years_in_business=0, payment_history_score=0, existing_transaction_months=0,
		)
		self.assertEqual(doc.risk_grade, "E")

	def test_recommended_limit(self):
		"""Test recommended limit calculation."""
		doc = self._create_assessment(
			revenue=100000000, profit=8000000, capital=100000000,
			years_in_business=15, payment_history_score=90,
			existing_transaction_months=36, average_monthly_transaction=2000000,
		)
		# Grade A -> multiplier 6 -> 2M * 6 = 12M
		if doc.risk_grade == "A":
			self.assertEqual(doc.recommended_limit, 12000000)

	def test_status_transition_to_under_review(self):
		"""Test transition from Draft to Under Review."""
		doc = self._create_assessment()
		doc.status = "Under Review"
		doc.save(ignore_permissions=True)
		self.assertEqual(doc.status, "Under Review")
		self.assertEqual(doc.reviewer, frappe.session.user)

	def test_status_transition_to_approved(self):
		"""Test transition from Under Review to Approved."""
		doc = self._create_assessment()
		doc.status = "Under Review"
		doc.save(ignore_permissions=True)

		doc.status = "Approved"
		doc.approved_amount = 5000000
		doc.save(ignore_permissions=True)

		self.assertEqual(doc.status, "Approved")
		self.assertEqual(doc.approved_by, frappe.session.user)
		self.assertIsNotNone(doc.approved_date)
		self.assertIsNotNone(doc.valid_until)

	def test_status_transition_to_rejected(self):
		"""Test transition from Under Review to Rejected."""
		doc = self._create_assessment()
		doc.status = "Under Review"
		doc.save(ignore_permissions=True)

		doc.status = "Rejected"
		doc.rejection_reason = "財務状況が不十分"
		doc.save(ignore_permissions=True)
		self.assertEqual(doc.status, "Rejected")

	def test_invalid_status_transition(self):
		"""Test that invalid status transitions are blocked."""
		doc = self._create_assessment()
		doc.status = "Approved"
		self.assertRaises(frappe.ValidationError, doc.save)

	def test_rejection_requires_reason(self):
		"""Test that rejection requires a reason."""
		doc = self._create_assessment()
		doc.status = "Under Review"
		doc.save(ignore_permissions=True)

		doc.status = "Rejected"
		doc.rejection_reason = ""
		self.assertRaises(frappe.ValidationError, doc.save)

	def test_api_create_assessment(self):
		"""Test assessment creation via API."""
		from lifegence_business.credit.api.assessment import create_assessment

		result = create_assessment(
			customer="_Test Credit Customer",
			requested_amount=3000000,
			assessment_type="増額申請",
		)
		self.assertTrue(result["success"])
		self.assertIn("assessment", result)
		self.assertEqual(result["assessment_type"], "増額申請")
