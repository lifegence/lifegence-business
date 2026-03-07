# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CreditAlert(Document):
	def before_save(self):
		if self.current_value and self.threshold_value:
			excess = (self.current_value or 0) - (self.threshold_value or 0)
			self.excess_amount = excess if excess > 0 else 0
