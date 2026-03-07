# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import hashlib
import os

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_years, getdate, now_datetime


class ManagedDocument(Document):
	def before_insert(self):
		self._detect_file_info()
		self._generate_content_hash()
		self._create_initial_version()
		self._calculate_retention_date()

	def validate(self):
		self._validate_finalized()
		self._validate_status_transition()

	def _detect_file_info(self):
		"""Auto-detect file type and size from the attached file."""
		if self.file:
			ext = os.path.splitext(self.file)[1].lower().lstrip(".")
			self.file_type = ext if ext else "unknown"

			file_doc = frappe.get_all(
				"File",
				filters={"file_url": self.file},
				fields=["file_size"],
				limit=1,
			)
			if file_doc:
				self.file_size = file_doc[0].file_size

	def _generate_content_hash(self):
		"""Generate SHA-256 hash of file content for integrity verification."""
		if not self.file:
			return

		file_doc = frappe.get_all(
			"File",
			filters={"file_url": self.file},
			fields=["name", "file_url", "is_private"],
			limit=1,
		)
		if not file_doc:
			return

		try:
			file_path = frappe.get_doc("File", file_doc[0].name).get_full_path()
			if os.path.exists(file_path):
				sha256 = hashlib.sha256()
				with open(file_path, "rb") as f:
					for chunk in iter(lambda: f.read(8192), b""):
						sha256.update(chunk)
				self.content_hash = sha256.hexdigest()
		except Exception:
			frappe.log_error("DMS: Failed to generate content hash")

	def _create_initial_version(self):
		"""Create version 1 entry on first save."""
		if not self.versions:
			self.append("versions", {
				"version_number": 1,
				"file": self.file,
				"change_summary": "初版作成",
				"changed_by": frappe.session.user,
				"changed_on": now_datetime(),
			})
			self.current_version = 1

	def _calculate_retention_date(self):
		"""Calculate retention date based on linked policy."""
		if self.retention_policy:
			policy = frappe.get_doc("Retention Policy", self.retention_policy)
			if policy.retention_years > 0:
				self.retention_until = add_years(getdate(), policy.retention_years)
			else:
				self.retention_until = None  # Permanent retention

	def _validate_finalized(self):
		"""Prevent modifications to finalized documents."""
		if self.is_new():
			return

		old_doc = self.get_doc_before_save()
		if old_doc and old_doc.is_finalized:
			# Allow only status change to Archived
			if self.status != old_doc.status and self.status == "Archived":
				return
			# Check if any substantive field changed
			check_fields = ["document_name", "file", "document_type", "folder", "tags", "description"]
			for field in check_fields:
				if self.get(field) != old_doc.get(field):
					frappe.throw(_("確定済み文書は変更できません。"))
			# Check if new versions were added
			if len(self.versions) > len(old_doc.versions):
				frappe.throw(_("確定済み文書にバージョンを追加することはできません。"))

	def _validate_status_transition(self):
		"""Validate document status transitions."""
		if self.is_new():
			return

		old_doc = self.get_doc_before_save()
		if not old_doc or old_doc.status == self.status:
			return

		valid_transitions = {
			"Draft": ["Active", "Under Review", "Archived"],
			"Active": ["Under Review", "Archived"],
			"Under Review": ["Active", "Archived"],
			"Archived": [],
		}

		allowed = valid_transitions.get(old_doc.status, [])
		if self.status not in allowed:
			frappe.throw(
				_("ステータスを {0} から {1} に変更することはできません。").format(
					old_doc.status, self.status
				)
			)

	def add_new_version(self, file_url, change_summary=""):
		"""Add a new version to the document."""
		if self.is_finalized:
			frappe.throw(_("確定済み文書にバージョンを追加することはできません。"))

		new_version = self.current_version + 1
		self.append("versions", {
			"version_number": new_version,
			"file": file_url,
			"change_summary": change_summary,
			"changed_by": frappe.session.user,
			"changed_on": now_datetime(),
		})
		self.current_version = new_version
		self.file = file_url
		self._detect_file_info()
		self._generate_content_hash()
		self.save(ignore_permissions=True)

	def finalize(self):
		"""Mark document as finalized (immutable)."""
		if self.is_finalized:
			frappe.throw(_("この文書は既に確定済みです。"))
		self.is_finalized = 1
		self.status = "Active"
		self._generate_content_hash()
		self.save(ignore_permissions=True)

		# Create e-book preservation log if enabled
		settings = frappe.get_single("DMS Settings")
		if settings.e_book_preservation_enabled:
			frappe.get_doc({
				"doctype": "E-Book Preservation Log",
				"document": self.name,
				"event_type": "Finalized",
				"content_hash": self.content_hash,
				"timestamp": now_datetime(),
				"verified_by": frappe.session.user,
			}).insert(ignore_permissions=True)

	def after_insert(self):
		"""Create e-book preservation log on document creation if enabled."""
		settings = frappe.get_single("DMS Settings")
		if settings.e_book_preservation_enabled:
			frappe.get_doc({
				"doctype": "E-Book Preservation Log",
				"document": self.name,
				"event_type": "Created",
				"content_hash": self.content_hash,
				"timestamp": now_datetime(),
				"verified_by": frappe.session.user,
			}).insert(ignore_permissions=True)
