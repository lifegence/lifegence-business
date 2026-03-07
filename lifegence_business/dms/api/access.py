# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import now_datetime


@frappe.whitelist()
def log_document_access(document, access_type="View"):
	"""Log a document access event (View/Download/Print)."""
	if not frappe.db.exists("Managed Document", document):
		return {"success": False, "error": _("文書 {0} は存在しません。").format(document)}

	if access_type not in ("View", "Download", "Print"):
		return {"success": False, "error": _("無効なアクセス種別です。")}

	# Check if access logging is enabled
	settings = frappe.get_single("DMS Settings")
	if not settings.enable_access_logging:
		return {"success": True, "message": "アクセスログは無効です。"}

	log = frappe.get_doc({
		"doctype": "Document Access Log",
		"document": document,
		"access_type": access_type,
		"user": frappe.session.user,
		"accessed_on": now_datetime(),
		"ip_address": frappe.local.request_ip if hasattr(frappe.local, "request_ip") else None,
	})
	log.insert(ignore_permissions=True)

	return {
		"success": True,
		"log": log.name,
		"document": document,
		"access_type": access_type,
	}
