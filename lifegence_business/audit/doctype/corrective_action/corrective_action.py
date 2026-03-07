# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today


class CorrectiveAction(Document):
	def before_save(self):
		if self.status == "Completed" and not self.completion_date:
			self.completion_date = today()
