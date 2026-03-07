# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, today


class BudgetPlan(Document):
	def before_save(self):
		self._calculate_totals()
		self._set_prepared_info()

	def validate(self):
		self._validate_status_transition()

	def _calculate_totals(self):
		"""Calculate total_annual_amount from items."""
		self.total_annual_amount = sum(flt(item.annual_total) for item in self.items)

	def _set_prepared_info(self):
		"""Auto-set prepared_by and prepared_date."""
		if not self.prepared_by:
			self.prepared_by = frappe.session.user
		if not self.prepared_date:
			self.prepared_date = today()

	def _validate_status_transition(self):
		"""Validate status transitions."""
		if self.is_new():
			return

		old_status = frappe.db.get_value("Budget Plan", self.name, "status")
		if not old_status or old_status == self.status:
			return

		valid_transitions = {
			"Draft": ["Submitted", "Cancelled"],
			"Submitted": ["Approved", "Rejected", "Cancelled"],
			"Approved": ["Revised"],
			"Rejected": ["Draft"],
			"Revised": [],
			"Cancelled": [],
		}

		allowed = valid_transitions.get(old_status, [])
		if self.status not in allowed:
			frappe.throw(
				f"ステータスを {old_status} から {self.status} に変更できません。"
				f"許可される遷移先: {', '.join(allowed) or 'なし'}",
				frappe.ValidationError,
			)

		if self.status == "Rejected" and not self.rejection_reason:
			frappe.throw("差戻理由を入力してください。", frappe.ValidationError)

		if self.status == "Approved":
			self.approved_by = frappe.session.user
			self.approved_date = today()

	def update_actuals(self):
		"""Update actual amounts from GL Entry."""
		total_actual = 0
		for item in self.items:
			actual = frappe.db.sql("""
				SELECT SUM(debit - credit) as net_amount
				FROM `tabGL Entry`
				WHERE cost_center = %s AND account = %s
				  AND fiscal_year = %s AND company = %s AND is_cancelled = 0
			""", (self.cost_center, item.account, self.fiscal_year, self.company))
			item_actual = flt(actual[0][0]) if actual and actual[0][0] else 0
			total_actual += item_actual

		self.current_actual_amount = total_actual
		self.variance_amount = flt(self.total_annual_amount) - flt(self.current_actual_amount)
		if self.total_annual_amount:
			self.variance_pct = (flt(self.variance_amount) / flt(self.total_annual_amount)) * 100
		else:
			self.variance_pct = 0
