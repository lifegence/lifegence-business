# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestDocumentAccess(FrappeTestCase):
	"""Test cases for Document Access Rule and Access Log."""

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

		if not frappe.db.exists("Document Folder", "アクセステスト"):
			frappe.get_doc({
				"doctype": "Document Folder",
				"folder_name": "アクセステスト",
				"description": "アクセス制御テスト用フォルダ",
				"enabled": 1,
			}).insert(ignore_permissions=True)
		frappe.db.commit()

	def _create_test_file(self):
		file_doc = frappe.get_doc({
			"doctype": "File",
			"file_name": f"test_acc_{frappe.generate_hash(length=6)}.txt",
			"content": b"Access test content.",
			"is_private": 1,
		})
		file_doc.insert(ignore_permissions=True)
		return file_doc.file_url

	def _create_document(self, **kwargs):
		file_url = self._create_test_file()
		defaults = {
			"doctype": "Managed Document",
			"document_name": "アクセステスト文書",
			"file": file_url,
			"document_type": "その他",
		}
		defaults.update(kwargs)
		doc = frappe.get_doc(defaults)
		doc.insert(ignore_permissions=True)
		return doc

	# ─── TC-ACC01: Create Access Rule ───────────────────────────────

	def test_create_access_rule(self):
		"""TC-ACC01: Create an access rule for a folder."""
		rule = frappe.get_doc({
			"doctype": "Document Access Rule",
			"folder": "アクセステスト",
			"rule_type": "User",
			"user": "Administrator",
			"access_level": "Full",
			"enabled": 1,
		})
		rule.insert(ignore_permissions=True)
		self.assertTrue(rule.name.startswith("DAR-"))
		self.assertEqual(rule.access_level, "Full")

	# ─── TC-ACC02: Access Rule by Role ──────────────────────────────

	def test_access_rule_by_role(self):
		"""TC-ACC02: Create a role-based access rule."""
		rule = frappe.get_doc({
			"doctype": "Document Access Rule",
			"folder": "アクセステスト",
			"rule_type": "Role",
			"role": "DMS Manager",
			"access_level": "Write",
			"enabled": 1,
		})
		rule.insert(ignore_permissions=True)
		self.assertEqual(rule.rule_type, "Role")
		self.assertEqual(rule.role, "DMS Manager")

	# ─── TC-ACC03: Access Rule by Department ────────────────────────

	def test_access_rule_by_department(self):
		"""TC-ACC03: Create a department-based access rule."""
		# Ensure a department exists
		if not frappe.db.exists("Department", {"name": ["like", "%テスト%"]}):
			# Use any existing department or skip
			departments = frappe.get_all("Department", limit=1)
			if not departments:
				self.skipTest("No departments available for testing")
			dept = departments[0].name
		else:
			dept = frappe.db.get_value(
				"Department", {"name": ["like", "%テスト%"]}, "name"
			)

		rule = frappe.get_doc({
			"doctype": "Document Access Rule",
			"folder": "アクセステスト",
			"rule_type": "Department",
			"department": dept,
			"access_level": "Read",
			"enabled": 1,
		})
		rule.insert(ignore_permissions=True)
		self.assertEqual(rule.rule_type, "Department")

	# ─── TC-ACC04: Access Log Creation ──────────────────────────────

	def test_access_log_creation(self):
		"""TC-ACC04: Access log is created for document access."""
		doc = self._create_document()
		log = frappe.get_doc({
			"doctype": "Document Access Log",
			"document": doc.name,
			"access_type": "View",
			"user": frappe.session.user,
			"accessed_on": frappe.utils.now_datetime(),
		})
		log.insert(ignore_permissions=True)

		self.assertTrue(log.name.startswith("DAL-"))
		self.assertEqual(log.access_type, "View")
		self.assertEqual(log.user, frappe.session.user)

	# ─── TC-ACC05: Access Log API ───────────────────────────────────

	def test_access_log_api(self):
		"""TC-ACC05: Log document access via API function."""
		from lifegence_business.dms.api.access import log_document_access

		doc = self._create_document()
		result = log_document_access(document=doc.name, access_type="Download")

		self.assertTrue(result["success"])
		self.assertEqual(result["access_type"], "Download")
		self.assertEqual(result["document"], doc.name)
