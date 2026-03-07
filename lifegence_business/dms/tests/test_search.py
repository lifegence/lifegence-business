# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestDocumentSearch(FrappeTestCase):
	"""Test cases for document search functionality."""

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

		# Create test folder for search tests
		if not frappe.db.exists("Document Folder", "検索テスト"):
			frappe.get_doc({
				"doctype": "Document Folder",
				"folder_name": "検索テスト",
				"description": "検索テスト用",
				"enabled": 1,
			}).insert(ignore_permissions=True)

		# Create test documents for search
		cls._create_search_test_docs()
		frappe.db.commit()

	@classmethod
	def _create_search_test_docs(cls):
		"""Create documents for search testing."""
		docs = [
			{"document_name": "検索用就業規則", "document_type": "規程", "folder": "検索テスト"},
			{"document_name": "検索用マニュアル", "document_type": "マニュアル", "folder": "検索テスト"},
			{"document_name": "検索用契約書", "document_type": "契約書"},
		]
		for doc_data in docs:
			# Check if already exists
			existing = frappe.get_all(
				"Managed Document",
				filters={"document_name": doc_data["document_name"]},
				limit=1,
			)
			if existing:
				continue
			file_doc = frappe.get_doc({
				"doctype": "File",
				"file_name": f"search_{frappe.generate_hash(length=6)}.txt",
				"content": b"Search test content.",
				"is_private": 1,
			})
			file_doc.insert(ignore_permissions=True)
			frappe.get_doc({
				"doctype": "Managed Document",
				"file": file_doc.file_url,
				**doc_data,
			}).insert(ignore_permissions=True)

	# ─── TC-SRC01: Search by Keyword ────────────────────────────────

	def test_search_by_keyword(self):
		"""TC-SRC01: Search documents by keyword."""
		from lifegence_dms.api.search import search_documents

		result = search_documents(query="就業規則")
		self.assertTrue(result["success"])
		self.assertGreaterEqual(result["count"], 1)
		names = [d["document_name"] for d in result["documents"]]
		self.assertIn("検索用就業規則", names)

	# ─── TC-SRC02: Search by Folder ─────────────────────────────────

	def test_search_by_folder(self):
		"""TC-SRC02: Search documents within a specific folder."""
		from lifegence_dms.api.search import search_documents

		result = search_documents(folder="検索テスト")
		self.assertTrue(result["success"])
		self.assertGreaterEqual(result["count"], 2)

	# ─── TC-SRC03: Search by Document Type ──────────────────────────

	def test_search_by_document_type(self):
		"""TC-SRC03: Filter documents by document type."""
		from lifegence_dms.api.search import search_documents

		result = search_documents(document_type="契約書")
		self.assertTrue(result["success"])
		for doc in result["documents"]:
			self.assertEqual(doc["document_type"], "契約書")
