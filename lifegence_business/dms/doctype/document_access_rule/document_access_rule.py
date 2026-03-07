# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class DocumentAccessRule(Document):
	def validate(self):
		self._validate_target()
		self._validate_assignee()

	def _validate_target(self):
		"""Ensure at least folder or document is specified."""
		if not self.folder and not self.document:
			frappe.throw(_("フォルダまたは文書のいずれかを指定してください。"))

	def _validate_assignee(self):
		"""Ensure the correct field is filled based on rule_type."""
		field_map = {"User": "user", "Role": "role", "Department": "department"}
		required_field = field_map.get(self.rule_type)
		if required_field and not self.get(required_field):
			frappe.throw(
				_("ルール種別が {0} の場合、{1} を指定してください。").format(
					self.rule_type, required_field
				)
			)
