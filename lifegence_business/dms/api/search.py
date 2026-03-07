# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe


@frappe.whitelist()
def search_documents(query=None, folder=None, document_type=None, tags=None):
	"""Search documents by keyword, folder, type, and tags."""
	filters = {}

	if folder:
		filters["folder"] = folder
	if document_type:
		filters["document_type"] = document_type

	or_filters = {}
	if query:
		or_filters = {
			"document_name": ["like", f"%{query}%"],
			"description": ["like", f"%{query}%"],
			"tags": ["like", f"%{query}%"],
		}

	if tags:
		if "tags" in or_filters:
			pass  # query already searches tags
		else:
			filters["tags"] = ["like", f"%{tags}%"]

	documents = frappe.get_all(
		"Managed Document",
		filters=filters,
		or_filters=or_filters if or_filters else None,
		fields=[
			"name", "document_name", "document_type", "status",
			"folder", "file_type", "tags", "current_version",
			"is_finalized", "creation", "modified",
		],
		order_by="modified desc",
		limit=50,
	)

	return {"success": True, "documents": documents, "count": len(documents)}
