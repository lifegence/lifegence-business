# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CreditLimitHistory(Document):
	def before_save(self):
		self.change_amount = (self.new_amount or 0) - (self.previous_amount or 0)
		if not self.changed_by:
			self.changed_by = frappe.session.user
