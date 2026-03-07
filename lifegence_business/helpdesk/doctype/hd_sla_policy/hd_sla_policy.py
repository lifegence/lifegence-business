# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class HDSLAPolicy(Document):
	def validate(self):
		self._validate_times()

	def _validate_times(self):
		"""Ensure response time < resolution time for each priority."""
		for priority in ("low", "medium", "high", "urgent"):
			response = self.get(f"{priority}_response_time") or 0
			resolution = self.get(f"{priority}_resolution_time") or 0
			if response > resolution:
				frappe.throw(
					_("{0}の応答時間は解決時間以下でなければなりません。").format(priority.capitalize())
				)
