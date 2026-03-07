# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

from frappe.model.document import Document
from frappe.utils import flt


class BudgetPlanItem(Document):
	def before_save(self):
		self._apply_distribution()
		self._calculate_annual_total()
		self._calculate_yoy_change()

	def _apply_distribution(self):
		"""Apply equal distribution if selected."""
		if self.distribution_method == "Equal" and flt(self.annual_total) > 0:
			monthly = flt(self.annual_total / 12, 0)
			remainder = flt(self.annual_total) - (monthly * 12)
			for i in range(1, 13):
				setattr(self, f"month_{i}", monthly)
			self.month_12 = monthly + remainder

	def _calculate_annual_total(self):
		"""Calculate annual total from monthly values."""
		self.annual_total = sum(
			flt(getattr(self, f"month_{i}", 0)) for i in range(1, 13)
		)

	def _calculate_yoy_change(self):
		"""Calculate year-over-year change percentage."""
		if flt(self.previous_year_actual):
			self.yoy_change_pct = (
				(flt(self.annual_total) - flt(self.previous_year_actual))
				/ flt(self.previous_year_actual) * 100
			)
		else:
			self.yoy_change_pct = 0
