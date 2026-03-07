# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class HDKnowledgeBase(Document):
	def before_insert(self):
		if not self.author:
			self.author = frappe.session.user
