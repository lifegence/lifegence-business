# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

from frappe.model.document import Document
from frappe.utils import flt


class BudgetForecastItem(Document):
	def before_save(self):
		self.forecast_annual = flt(self.actual_to_date) + flt(self.forecast_remaining)
		self.variance = flt(self.budget_amount) - flt(self.forecast_annual)
