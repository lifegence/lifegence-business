# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_years, getdate


class TestRetentionPolicy(FrappeTestCase):
	"""Test cases for Retention Policy and retention date calculation."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		for role_name in ("DMS Manager", "DMS User"):
			if not frappe.db.exists("Role", role_name):
				frappe.get_doc({
					"doctype": "Role",
					"role_name": role_name,
					"desk_access": 1,
				}).insert(ignore_permissions=True)

		settings = frappe.get_single("DMS Settings")
		settings.enable_version_control = 1
		settings.enable_access_logging = 1
		settings.e_book_preservation_enabled = 0
		settings.save(ignore_permissions=True)

		if not frappe.db.exists("Retention Policy", "テスト7年保存"):
			frappe.get_doc({
				"doctype": "Retention Policy",
				"policy_name": "テスト7年保存",
				"retention_years": 7,
				"action_on_expiry": "Notify",
				"enabled": 1,
			}).insert(ignore_permissions=True)
		if not frappe.db.exists("Retention Policy", "テスト永久保存"):
			frappe.get_doc({
				"doctype": "Retention Policy",
				"policy_name": "テスト永久保存",
				"retention_years": 0,
				"action_on_expiry": "Notify",
				"enabled": 1,
			}).insert(ignore_permissions=True)
		frappe.db.commit()

	def _create_test_file(self):
		file_doc = frappe.get_doc({
			"doctype": "File",
			"file_name": f"test_ret_{frappe.generate_hash(length=6)}.txt",
			"content": b"Retention test content.",
			"is_private": 1,
		})
		file_doc.insert(ignore_permissions=True)
		return file_doc.file_url

	def _create_document(self, **kwargs):
		file_url = self._create_test_file()
		defaults = {
			"doctype": "Managed Document",
			"document_name": "保存テスト文書",
			"file": file_url,
			"document_type": "その他",
		}
		defaults.update(kwargs)
		doc = frappe.get_doc(defaults)
		doc.insert(ignore_permissions=True)
		return doc

	# ─── TC-RET01: Create Retention Policy ──────────────────────────

	def test_create_retention_policy(self):
		"""TC-RET01: Create a retention policy."""
		self.assertTrue(frappe.db.exists("Retention Policy", "テスト7年保存"))
		policy = frappe.get_doc("Retention Policy", "テスト7年保存")
		self.assertEqual(policy.retention_years, 7)
		self.assertEqual(policy.action_on_expiry, "Notify")

	# ─── TC-RET02: Retention Date Calculation ───────────────────────

	def test_retention_date_calculation(self):
		"""TC-RET02: Retention date is calculated from creation + years."""
		doc = self._create_document(retention_policy="テスト7年保存")
		expected_date = add_years(getdate(), 7)
		self.assertEqual(getdate(doc.retention_until), expected_date)

	# ─── TC-RET03: Permanent Retention ──────────────────────────────

	def test_permanent_retention(self):
		"""TC-RET03: Permanent retention (years=0) has no expiry date."""
		doc = self._create_document(retention_policy="テスト永久保存")
		self.assertIsNone(doc.retention_until)

	# ─── TC-RET04: Check Retention Status API ───────────────────────

	def test_check_retention_status_api(self):
		"""TC-RET04: Check retention status via API."""
		from lifegence_business.dms.api.retention import check_retention_status

		doc = self._create_document(retention_policy="テスト7年保存")
		result = check_retention_status(document=doc.name)

		self.assertTrue(result["success"])
		self.assertEqual(result["retention_policy"], "テスト7年保存")
		self.assertFalse(result["is_expired"])
		self.assertFalse(result["is_permanent"])
		self.assertIn("days_remaining", result)
