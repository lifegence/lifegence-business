# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import nowdate, add_days

from lifegence_business.credit.services.risk_scoring import (
	calculate_risk_score,
	determine_grade,
	calculate_recommended_limit,
)


class CreditAssessment(Document):
	def validate(self):
		self._validate_status_transition()

	def before_save(self):
		self._run_risk_assessment()

	def on_update(self):
		if self.status == "Approved":
			self._create_or_update_credit_limit()
			self._record_history()
			self._update_customer_fields()

	def _validate_status_transition(self):
		"""Validate status transitions: Draft -> Under Review -> Approved/Rejected."""
		if self.is_new():
			return

		old_status = self.get_db_value("status")
		if old_status == self.status:
			return

		valid_transitions = {
			"Draft": ["Under Review"],
			"Under Review": ["Approved", "Rejected"],
		}
		allowed = valid_transitions.get(old_status, [])
		if self.status not in allowed:
			frappe.throw(
				_("ステータスを {0} から {1} に変更できません。").format(old_status, self.status)
			)

		if self.status == "Under Review":
			self.reviewer = frappe.session.user

		if self.status == "Approved":
			self.approved_by = frappe.session.user
			self.approved_date = nowdate()
			if not self.approved_amount:
				self.approved_amount = self.requested_amount
			settings = frappe.get_single("Credit Settings")
			self.valid_until = add_days(nowdate(), settings.default_credit_period_days or 365)

		if self.status == "Rejected" and not self.rejection_reason:
			frappe.throw(_("却下する場合は却下理由を入力してください。"))

	def _run_risk_assessment(self):
		"""Calculate risk score, grade, and recommended limit using shared service."""
		result = calculate_risk_score(
			revenue=self.revenue or 0,
			profit=self.profit,
			capital=self.capital or 0,
			years_in_business=self.years_in_business or 0,
			payment_history_score=self.payment_history_score or 0,
			existing_transaction_months=self.existing_transaction_months or 0,
			average_monthly_transaction=self.average_monthly_transaction or 0,
		)
		self.risk_score = result["score"]
		self.risk_grade = result["grade"]
		self.recommended_limit = result["recommended_limit"]

	def _create_or_update_credit_limit(self):
		"""Create or update Credit Limit on approval."""
		if not self.approved_amount:
			return

		company = self.company or frappe.defaults.get_defaults().get("company")
		if not company:
			return

		existing = frappe.db.exists(
			"Credit Limit",
			{"customer": self.customer, "company": company},
		)

		if existing:
			cl = frappe.get_doc("Credit Limit", existing)
			cl.credit_limit_amount = self.approved_amount
			cl.status = "Active"
			cl.valid_from = nowdate()
			cl.valid_until = self.valid_until
			cl.latest_assessment = self.name
			cl.risk_grade = self.risk_grade
			settings = frappe.get_single("Credit Settings")
			cl.review_cycle_months = settings.review_cycle_months or 12
			cl.last_review_date = nowdate()
			cl.next_review_date = add_days(nowdate(), (settings.review_cycle_months or 12) * 30)
			cl.save(ignore_permissions=True)
		else:
			settings = frappe.get_single("Credit Settings")
			cl = frappe.get_doc({
				"doctype": "Credit Limit",
				"customer": self.customer,
				"company": company,
				"credit_limit_amount": self.approved_amount,
				"status": "Active",
				"valid_from": nowdate(),
				"valid_until": self.valid_until,
				"latest_assessment": self.name,
				"risk_grade": self.risk_grade,
				"review_cycle_months": settings.review_cycle_months or 12,
				"last_review_date": nowdate(),
				"next_review_date": add_days(nowdate(), (settings.review_cycle_months or 12) * 30),
			})
			cl.insert(ignore_permissions=True)

	def _record_history(self):
		"""Record credit limit change in history."""
		company = self.company or frappe.defaults.get_defaults().get("company")
		if not company:
			return

		cl_name = frappe.db.get_value(
			"Credit Limit",
			{"customer": self.customer, "company": company},
			"name",
		)
		if not cl_name:
			return

		change_reason_map = {
			"新規取引": "新規設定",
			"定期見直し": "定期見直し",
			"増額申請": "増額承認",
			"緊急審査": "緊急変更",
		}

		previous = frappe.db.get_value(
			"Credit Limit History",
			{"credit_limit": cl_name},
			"new_amount",
			order_by="change_date desc",
		) or 0

		frappe.get_doc({
			"doctype": "Credit Limit History",
			"credit_limit": cl_name,
			"customer": self.customer,
			"company": company,
			"previous_amount": previous,
			"new_amount": self.approved_amount,
			"change_reason": change_reason_map.get(self.assessment_type, "新規設定"),
			"change_detail": self.review_comment or "",
			"assessment": self.name,
			"changed_by": frappe.session.user,
		}).insert(ignore_permissions=True)

	def _update_customer_fields(self):
		"""Update Customer custom fields with latest assessment results."""
		frappe.db.set_value("Customer", self.customer, {
			"risk_grade": self.risk_grade,
			"credit_status": "Active",
		}, update_modified=False)
