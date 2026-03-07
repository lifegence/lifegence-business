# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class DocumentFolder(Document):
	def validate(self):
		self._validate_no_circular_reference()

	def _validate_no_circular_reference(self):
		"""Prevent circular parent-child folder references."""
		if not self.parent_folder:
			return
		if self.parent_folder == self.name:
			frappe.throw(_("フォルダを自身の親フォルダに設定することはできません。"))

		visited = {self.name}
		current = self.parent_folder
		while current:
			if current in visited:
				frappe.throw(_("フォルダ階層に循環参照があります。"))
			visited.add(current)
			current = frappe.db.get_value("Document Folder", current, "parent_folder")
