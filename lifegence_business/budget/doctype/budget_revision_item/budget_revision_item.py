# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

from frappe.model.document import Document
from frappe.utils import flt


class BudgetRevisionItem(Document):
	def before_save(self):
		self._calculate_revised_total()
		self._calculate_change_amount()

	def _calculate_revised_total(self):
		"""Calculate revised annual total from monthly values."""
		total = sum(flt(getattr(self, f"revised_month_{i}", 0)) for i in range(1, 13))
		if total > 0:
			self.revised_annual_total = total

	def _calculate_change_amount(self):
		"""Calculate change amount."""
		self.change_amount = flt(self.revised_annual_total) - flt(self.original_annual_total)
