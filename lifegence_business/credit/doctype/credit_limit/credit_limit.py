# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class CreditLimit(Document):
	def validate(self):
		self._check_duplicate()

	def before_save(self):
		self.recalculate_balance()

	def _check_duplicate(self):
		"""Check for duplicate customer + company combination."""
		if self.is_new():
			existing = frappe.db.exists(
				"Credit Limit",
				{"customer": self.customer, "company": self.company, "name": ["!=", self.name]},
			)
			if existing:
				frappe.throw(
					_("取引先 {0} / 会社 {1} の与信枠は既に存在します: {2}").format(
						self.customer, self.company, existing
					)
				)

	def recalculate_balance(self):
		"""Recalculate used_amount from Sales Orders and Sales Invoices."""
		# Outstanding Sales Order balance (submitted, not completed/cancelled/closed)
		so_balance = frappe.db.sql(
			"""
			SELECT COALESCE(SUM(grand_total - advance_paid), 0)
			FROM `tabSales Order`
			WHERE customer = %s AND company = %s
			AND docstatus = 1
			AND status NOT IN ('Completed', 'Cancelled', 'Closed')
			""",
			(self.customer, self.company),
		)[0][0] or 0

		# Outstanding Sales Invoice balance
		si_balance = frappe.db.sql(
			"""
			SELECT COALESCE(SUM(outstanding_amount), 0)
			FROM `tabSales Invoice`
			WHERE customer = %s AND company = %s
			AND docstatus = 1
			AND outstanding_amount > 0
			""",
			(self.customer, self.company),
		)[0][0] or 0

		self.used_amount = so_balance + si_balance
		self.available_amount = max((self.credit_limit_amount or 0) - self.used_amount, 0)
		if self.credit_limit_amount and self.credit_limit_amount > 0:
			self.usage_percentage = round((self.used_amount / self.credit_limit_amount) * 100, 2)
		else:
			self.usage_percentage = 0

	def check_credit(self, additional_amount=0):
		"""Check if credit limit allows the additional amount."""
		self.recalculate_balance()
		total_after = self.used_amount + additional_amount
		if total_after > (self.credit_limit_amount or 0):
			return {
				"allowed": False,
				"used_amount": self.used_amount,
				"credit_limit": self.credit_limit_amount,
				"additional": additional_amount,
				"total_after": total_after,
				"excess": total_after - self.credit_limit_amount,
			}
		return {"allowed": True, "used_amount": self.used_amount, "available": self.available_amount}
