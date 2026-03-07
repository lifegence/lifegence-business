# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe


@frappe.whitelist()
def get_folder_tree(parent_folder=None):
	"""Get folder hierarchy tree. If parent_folder is None, returns root folders."""
	filters = {"enabled": 1}
	if parent_folder:
		filters["parent_folder"] = parent_folder
	else:
		filters["parent_folder"] = ("is", "not set")

	folders = frappe.get_all(
		"Document Folder",
		filters=filters,
		fields=[
			"name", "folder_name", "parent_folder",
			"department", "is_private", "description",
		],
		order_by="folder_name asc",
	)

	for folder in folders:
		child_count = frappe.db.count(
			"Document Folder",
			filters={"parent_folder": folder["name"], "enabled": 1},
		)
		doc_count = frappe.db.count(
			"Managed Document",
			filters={"folder": folder["name"]},
		)
		folder["child_count"] = child_count
		folder["document_count"] = doc_count

	return {"success": True, "folders": folders, "count": len(folders)}
