# Copyright (c) 2025, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ComplianceSettings(Document):
	@staticmethod
	def get_gemini_api_key():
		"""Get decrypted Gemini API key. Falls back to Company OS AI Settings."""
		settings = frappe.get_single("Compliance Settings")
		key = settings.get_password("gemini_api_key")
		if key:
			return key
		try:
			cos = frappe.get_single("Company OS AI Settings")
			return cos.get_password("gemini_api_key")
		except Exception:
			return None

	def validate(self):
		if self.vector_weight and self.fulltext_weight:
			total = float(self.vector_weight) + float(self.fulltext_weight)
			if abs(total - 1.0) > 0.01:
				frappe.throw("Vector Weight + Full-text Weight must equal 1.0")

		if self.chunk_size and self.chunk_overlap:
			if int(self.chunk_overlap) >= int(self.chunk_size):
				frappe.throw("Chunk Overlap must be less than Chunk Size")
