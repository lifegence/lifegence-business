# Copyright (c) 2025, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CommitteeReport(Document):
	def validate(self):
		if self.year and (self.year < 2000 or self.year > 2100):
			frappe.throw("Year must be between 2000 and 2100")

	def on_trash(self):
		# Delete associated chunks
		frappe.db.delete("Report Chunk", {"report": self.name})
		# Delete associated indexing logs
		frappe.db.delete("Indexing Log", {"report": self.name})
