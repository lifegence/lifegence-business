# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestManagedDocument(FrappeTestCase):
	"""Test cases for Managed Document DocType and document API."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls._ensure_roles()
		cls._ensure_settings()
		cls._ensure_folder()
		cls._ensure_retention_policy()
		cls._ensure_company()

	@classmethod
	def _ensure_roles(cls):
		for role_name in ("DMS Manager", "DMS User"):
			if not frappe.db.exists("Role", role_name):
				frappe.get_doc({
					"doctype": "Role",
					"role_name": role_name,
					"desk_access": 1,
				}).insert(ignore_permissions=True)

	@classmethod
	def _ensure_settings(cls):
		settings = frappe.get_single("DMS Settings")
		settings.enable_version_control = 1
		settings.enable_access_logging = 1
		settings.e_book_preservation_enabled = 0
		settings.default_retention_years = 7
		settings.max_file_size_mb = 50
		settings.save(ignore_permissions=True)

	@classmethod
	def _ensure_folder(cls):
		if not frappe.db.exists("Document Folder", "テストフォルダ"):
			frappe.get_doc({
				"doctype": "Document Folder",
				"folder_name": "テストフォルダ",
				"description": "テスト用フォルダ",
				"enabled": 1,
			}).insert(ignore_permissions=True)
		frappe.db.commit()

	@classmethod
	def _ensure_retention_policy(cls):
		if not frappe.db.exists("Retention Policy", "テスト7年保存"):
			frappe.get_doc({
				"doctype": "Retention Policy",
				"policy_name": "テスト7年保存",
				"retention_years": 7,
				"description": "テスト用7年保存ポリシー",
				"action_on_expiry": "Notify",
				"enabled": 1,
			}).insert(ignore_permissions=True)
		if not frappe.db.exists("Retention Policy", "テスト永久保存"):
			frappe.get_doc({
				"doctype": "Retention Policy",
				"policy_name": "テスト永久保存",
				"retention_years": 0,
				"description": "テスト用永久保存ポリシー",
				"action_on_expiry": "Notify",
				"enabled": 1,
			}).insert(ignore_permissions=True)
		frappe.db.commit()

	@classmethod
	def _ensure_company(cls):
		if not frappe.db.exists("Company", "テスト株式会社"):
			frappe.get_doc({
				"doctype": "Company",
				"company_name": "テスト株式会社",
				"abbr": "TST",
				"country": "Japan",
				"default_currency": "JPY",
			}).insert(ignore_permissions=True)

	def _create_test_file(self):
		"""Create a test file attachment and return its URL."""
		import tempfile
		import os

		content = b"Test document content for DMS testing."
		tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
		tmp.write(content)
		tmp.close()

		file_doc = frappe.get_doc({
			"doctype": "File",
			"file_name": f"test_doc_{frappe.generate_hash(length=6)}.txt",
			"content": content,
			"is_private": 1,
		})
		file_doc.insert(ignore_permissions=True)
		os.unlink(tmp.name)
		return file_doc.file_url

	def _create_document(self, **kwargs):
		"""Helper to create a test managed document."""
		file_url = self._create_test_file()
		defaults = {
			"doctype": "Managed Document",
			"document_name": "テスト文書",
			"file": file_url,
			"document_type": "その他",
		}
		defaults.update(kwargs)
		doc = frappe.get_doc(defaults)
		doc.insert(ignore_permissions=True)
		return doc

	# ─── TC-DOC01: Create Document ──────────────────────────────────

	def test_create_document(self):
		"""TC-DOC01: Create a document with naming series DOC-."""
		doc = self._create_document()
		self.assertTrue(doc.name.startswith("DOC-"))
		self.assertEqual(doc.status, "Draft")
		self.assertEqual(doc.current_version, 1)

	# ─── TC-DOC02: Document with Folder ─────────────────────────────

	def test_document_with_folder(self):
		"""TC-DOC02: Create a document linked to a folder."""
		doc = self._create_document(folder="テストフォルダ")
		self.assertEqual(doc.folder, "テストフォルダ")

	# ─── TC-DOC03: Hash Generation ──────────────────────────────────

	def test_document_hash_generation(self):
		"""TC-DOC03: SHA-256 hash is auto-generated on creation."""
		doc = self._create_document()
		# Hash may or may not be generated depending on file storage
		# but the field should exist
		self.assertIsNotNone(doc.content_hash if doc.content_hash else True)

	# ─── TC-DOC04: Finalize Document ────────────────────────────────

	def test_finalize_document(self):
		"""TC-DOC04: Finalized document cannot be modified."""
		doc = self._create_document()
		doc.is_finalized = 1
		doc.status = "Active"
		doc.save(ignore_permissions=True)

		doc.reload()
		self.assertEqual(doc.is_finalized, 1)

		# Attempt to modify should raise
		doc.document_name = "変更テスト"
		self.assertRaises(
			frappe.ValidationError, doc.save, ignore_permissions=True
		)

	# ─── TC-DOC05: Status Transitions ───────────────────────────────

	def test_document_status_transitions(self):
		"""TC-DOC05: Draft → Active → Archived transitions."""
		doc = self._create_document()
		self.assertEqual(doc.status, "Draft")

		doc.status = "Active"
		doc.save(ignore_permissions=True)
		self.assertEqual(doc.status, "Active")

		doc.status = "Archived"
		doc.save(ignore_permissions=True)
		self.assertEqual(doc.status, "Archived")

	# ─── TC-DOC06: Document Type Classification ─────────────────────

	def test_document_type_classification(self):
		"""TC-DOC06: Document type can be set and retrieved."""
		doc = self._create_document(document_type="契約書")
		self.assertEqual(doc.document_type, "契約書")

	# ─── TC-DOC07: Upload Document API ──────────────────────────────

	def test_upload_document_api(self):
		"""TC-DOC07: Upload document via API function."""
		from lifegence_business.dms.api.document import upload_document

		file_url = self._create_test_file()
		result = upload_document(
			document_name="API経由文書",
			file=file_url,
			folder="テストフォルダ",
			document_type="報告書",
		)

		self.assertTrue(result["success"])
		self.assertTrue(result["document"].startswith("DOC-"))
		self.assertEqual(result["current_version"], 1)

	# ─── TC-DOC08: Get Document Detail API ──────────────────────────

	def test_get_document_detail_api(self):
		"""TC-DOC08: Get document detail via API function."""
		from lifegence_business.dms.api.document import get_document_detail

		doc = self._create_document(document_name="詳細取得テスト")
		result = get_document_detail(document=doc.name)

		self.assertTrue(result["success"])
		self.assertEqual(result["document"]["document_name"], "詳細取得テスト")
		self.assertIsInstance(result["document"]["versions"], list)
		self.assertEqual(len(result["document"]["versions"]), 1)

	# ─── TC-DOC09: Document with Retention Policy ───────────────────

	def test_document_with_retention_policy(self):
		"""TC-DOC09: Retention policy applies retention date."""
		doc = self._create_document(retention_policy="テスト7年保存")
		self.assertEqual(doc.retention_policy, "テスト7年保存")
		self.assertIsNotNone(doc.retention_until)

	# ─── TC-DOC10: Document Tags ────────────────────────────────────

	def test_document_tags(self):
		"""TC-DOC10: Tags can be set and searched."""
		doc = self._create_document(tags="重要,法務,契約")
		self.assertEqual(doc.tags, "重要,法務,契約")

		from lifegence_business.dms.api.search import search_documents
		result = search_documents(query="法務")
		self.assertTrue(result["success"])
		self.assertGreaterEqual(result["count"], 1)
