# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import now_datetime
from frappe.model.document import Document


class DocumentReview(Document):
	def before_insert(self):
		if not self.requested_by:
			self.requested_by = frappe.session.user

	def validate(self):
		self._set_reviewed_on()

	def _set_reviewed_on(self):
		"""Set reviewed_on when status changes to Approved or Rejected."""
		if self.is_new():
			return

		old_doc = self.get_doc_before_save()
		if not old_doc:
			return

		if old_doc.status == "Pending" and self.status in ("Approved", "Rejected"):
			self.reviewed_on = now_datetime()
