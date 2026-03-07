# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today


class AuditChecklist(Document):
	def before_save(self):
		if self.is_new():
			self.prepared_by = self.prepared_by or frappe.session.user
			self.preparation_date = self.preparation_date or today()
		self.update_summary()

	def update_summary(self):
		if not self.items:
			return
		self.total_items = len(self.items)
		self.conforming_items = sum(1 for i in self.items if i.result == "Conforming")
		self.non_conforming_items = sum(1 for i in self.items if i.result == "Non-conforming")
		self.not_applicable_items = sum(1 for i in self.items if i.result == "Not Applicable")
		self.not_tested_items = sum(1 for i in self.items if i.result == "Not Tested")
		tested = self.conforming_items + self.non_conforming_items
		self.conformance_rate = (self.conforming_items / tested * 100) if tested > 0 else 0
