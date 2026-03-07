# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, today


class BudgetRevision(Document):
	def before_save(self):
		self._populate_from_budget_plan()
		self._calculate_totals()
		if not self.requested_by:
			self.requested_by = frappe.session.user

	def validate(self):
		self._validate_budget_plan_status()

	def on_submit(self):
		self._apply_revision_to_budget_plan()

	def _populate_from_budget_plan(self):
		"""Auto-populate fields from the linked Budget Plan."""
		if self.budget_plan and not self.fiscal_year:
			bp = frappe.get_doc("Budget Plan", self.budget_plan)
			self.fiscal_year = bp.fiscal_year
			self.department = bp.department
			self.cost_center = bp.cost_center

	def _calculate_totals(self):
		"""Calculate total original, revised, and change amounts."""
		self.total_original_amount = sum(flt(item.original_annual_total) for item in self.revised_items)
		self.total_revised_amount = sum(flt(item.revised_annual_total) for item in self.revised_items)
		self.total_change_amount = flt(self.total_revised_amount) - flt(self.total_original_amount)

	def _validate_budget_plan_status(self):
		"""Ensure budget plan is in a revisable state."""
		if self.budget_plan:
			bp_status = frappe.db.get_value("Budget Plan", self.budget_plan, "status")
			if bp_status not in ("Approved", "Revised"):
				frappe.throw(
					f"予算計画のステータスが「{bp_status}」のため修正できません。"
					"承認済みまたは修正済みの予算計画のみ修正可能です。",
					frappe.ValidationError,
				)

	def _apply_revision_to_budget_plan(self):
		"""Apply revision to the Budget Plan when approved."""
		bp = frappe.get_doc("Budget Plan", self.budget_plan)

		for rev_item in self.revised_items:
			for bp_item in bp.items:
				if bp_item.account == rev_item.account:
					for i in range(1, 13):
						revised_val = flt(getattr(rev_item, f"revised_month_{i}", 0))
						if revised_val:
							setattr(bp_item, f"month_{i}", revised_val)
					bp_item.annual_total = flt(rev_item.revised_annual_total)
					break

		bp.status = "Revised"
		bp.amendments = (bp.amendments or 0) + 1
		bp.latest_revision = self.name
		bp.total_revised_amount = flt(self.total_revised_amount)
		bp.save(ignore_permissions=True)
