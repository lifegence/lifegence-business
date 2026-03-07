# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import today


class AuditFinding(Document):
	def before_save(self):
		if self.is_new():
			self.reported_by = self.reported_by or frappe.session.user
			self.finding_date = self.finding_date or today()

	def validate(self):
		self._validate_status_transition()

	def _validate_status_transition(self):
		if self.is_new():
			return
		old_status = self.get_db_value("status")
		if old_status == self.status:
			return

		if self.status == "Closed":
			self.closed_date = today()
			self.closed_by = frappe.session.user
