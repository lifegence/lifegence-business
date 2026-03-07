# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestDocumentVersion(FrappeTestCase):
	"""Test cases for Document Version management."""

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

	def _create_test_file(self, content=None):
		"""Create a test file and return its URL."""
		if content is None:
			content = b"Test file content."
		file_doc = frappe.get_doc({
			"doctype": "File",
			"file_name": f"test_ver_{frappe.generate_hash(length=6)}.txt",
			"content": content,
			"is_private": 1,
		})
		file_doc.insert(ignore_permissions=True)
		return file_doc.file_url

	def _create_document(self, **kwargs):
		"""Helper to create a test managed document."""
		file_url = self._create_test_file()
		defaults = {
			"doctype": "Managed Document",
			"document_name": "バージョンテスト文書",
			"file": file_url,
			"document_type": "その他",
		}
		defaults.update(kwargs)
		doc = frappe.get_doc(defaults)
		doc.insert(ignore_permissions=True)
		return doc

	# ─── TC-VER01: Initial Version ──────────────────────────────────

	def test_initial_version(self):
		"""TC-VER01: First version is auto-created on document creation."""
		doc = self._create_document()
		self.assertEqual(len(doc.versions), 1)
		self.assertEqual(doc.versions[0].version_number, 1)
		self.assertEqual(doc.versions[0].change_summary, "初版作成")

	# ─── TC-VER02: Create New Version ───────────────────────────────

	def test_create_new_version(self):
		"""TC-VER02: Add a new version to existing document."""
		doc = self._create_document()
		new_file = self._create_test_file(content=b"Updated content v2.")

		doc.add_new_version(file_url=new_file, change_summary="内容を更新")

		doc.reload()
		self.assertEqual(len(doc.versions), 2)
		self.assertEqual(doc.current_version, 2)

	# ─── TC-VER03: Version Number Increment ─────────────────────────

	def test_version_number_increment(self):
		"""TC-VER03: Version numbers auto-increment correctly."""
		doc = self._create_document()
		for i in range(2, 5):
			new_file = self._create_test_file(
				content=f"Content v{i}".encode()
			)
			doc.add_new_version(file_url=new_file, change_summary=f"v{i}に更新")

		doc.reload()
		self.assertEqual(doc.current_version, 4)
		for idx, v in enumerate(doc.versions):
			self.assertEqual(v.version_number, idx + 1)

	# ─── TC-VER04: Version Change Summary ───────────────────────────

	def test_version_change_summary(self):
		"""TC-VER04: Change summary is recorded for each version."""
		doc = self._create_document()
		new_file = self._create_test_file(content=b"Changed content.")

		doc.add_new_version(file_url=new_file, change_summary="誤字修正")

		doc.reload()
		self.assertEqual(doc.versions[1].change_summary, "誤字修正")
		self.assertEqual(doc.versions[1].changed_by, frappe.session.user)

	# ─── TC-VER05: Finalized No New Version ─────────────────────────

	def test_finalized_no_new_version(self):
		"""TC-VER05: Cannot add version to finalized document."""
		doc = self._create_document()
		doc.is_finalized = 1
		doc.status = "Active"
		doc.save(ignore_permissions=True)

		new_file = self._create_test_file(content=b"Attempt after finalize.")
		self.assertRaises(
			frappe.ValidationError,
			doc.add_new_version,
			file_url=new_file,
			change_summary="確定後の変更",
		)
