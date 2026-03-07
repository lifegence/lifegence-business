# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe import _


@frappe.whitelist()
def upload_document(
	document_name,
	file,
	folder=None,
	document_type="その他",
	tags=None,
	description=None,
	retention_policy=None,
	company=None,
):
	"""Upload a new managed document with hash generation and initial version."""
	doc = frappe.get_doc({
		"doctype": "Managed Document",
		"document_name": document_name,
		"file": file,
		"folder": folder,
		"document_type": document_type,
		"tags": tags,
		"description": description,
		"retention_policy": retention_policy,
		"company": company,
	})
	doc.insert(ignore_permissions=True)

	return {
		"success": True,
		"document": doc.name,
		"document_name": doc.document_name,
		"status": doc.status,
		"current_version": doc.current_version,
		"content_hash": doc.content_hash,
		"retention_until": str(doc.retention_until) if doc.retention_until else None,
	}


@frappe.whitelist()
def create_new_version(document, file, change_summary=""):
	"""Add a new version to an existing document."""
	if not frappe.db.exists("Managed Document", document):
		return {"success": False, "error": _("文書 {0} は存在しません。").format(document)}

	doc = frappe.get_doc("Managed Document", document)
	doc.add_new_version(file_url=file, change_summary=change_summary)

	return {
		"success": True,
		"document": doc.name,
		"current_version": doc.current_version,
		"content_hash": doc.content_hash,
	}


@frappe.whitelist()
def finalize_document(document):
	"""Finalize a document, making it immutable."""
	if not frappe.db.exists("Managed Document", document):
		return {"success": False, "error": _("文書 {0} は存在しません。").format(document)}

	doc = frappe.get_doc("Managed Document", document)
	doc.finalize()

	return {
		"success": True,
		"document": doc.name,
		"is_finalized": doc.is_finalized,
		"content_hash": doc.content_hash,
	}


@frappe.whitelist()
def get_document_detail(document):
	"""Get document details including version history and access rules."""
	if not frappe.db.exists("Managed Document", document):
		return {"success": False, "error": _("文書 {0} は存在しません。").format(document)}

	doc = frappe.get_doc("Managed Document", document)

	versions = []
	for v in doc.versions:
		versions.append({
			"version_number": v.version_number,
			"file": v.file,
			"change_summary": v.change_summary,
			"changed_by": v.changed_by,
			"changed_on": str(v.changed_on) if v.changed_on else None,
		})

	access_rules = frappe.get_all(
		"Document Access Rule",
		filters={"document": document, "enabled": 1},
		fields=["name", "rule_type", "user", "role", "department", "access_level"],
	)

	return {
		"success": True,
		"document": {
			"name": doc.name,
			"document_name": doc.document_name,
			"document_type": doc.document_type,
			"status": doc.status,
			"folder": doc.folder,
			"file": doc.file,
			"file_type": doc.file_type,
			"file_size": doc.file_size,
			"tags": doc.tags,
			"description": doc.description,
			"current_version": doc.current_version,
			"is_finalized": doc.is_finalized,
			"content_hash": doc.content_hash,
			"retention_policy": doc.retention_policy,
			"retention_until": str(doc.retention_until) if doc.retention_until else None,
			"company": doc.company,
			"versions": versions,
			"access_rules": access_rules,
		},
	}
