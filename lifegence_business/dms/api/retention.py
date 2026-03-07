# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate


@frappe.whitelist()
def check_retention_status(document):
	"""Check retention status for a document."""
	if not frappe.db.exists("Managed Document", document):
		return {"success": False, "error": _("文書 {0} は存在しません。").format(document)}

	doc = frappe.get_doc("Managed Document", document)

	result = {
		"success": True,
		"document": doc.name,
		"document_name": doc.document_name,
		"retention_policy": doc.retention_policy,
		"retention_until": str(doc.retention_until) if doc.retention_until else None,
		"is_expired": False,
		"is_permanent": False,
	}

	if not doc.retention_policy:
		result["message"] = "保存ポリシーが設定されていません。"
		return result

	policy = frappe.get_doc("Retention Policy", doc.retention_policy)
	result["policy_name"] = policy.policy_name
	result["retention_years"] = policy.retention_years
	result["action_on_expiry"] = policy.action_on_expiry

	if policy.retention_years == 0:
		result["is_permanent"] = True
		result["message"] = "永久保存文書です。"
	elif doc.retention_until:
		today = getdate()
		retention_date = getdate(doc.retention_until)
		result["is_expired"] = today > retention_date
		if result["is_expired"]:
			result["message"] = f"保存期限を超過しています（期限: {doc.retention_until}）。"
		else:
			days_remaining = (retention_date - today).days
			result["days_remaining"] = days_remaining
			result["message"] = f"保存期限まで残り{days_remaining}日です。"

	return result
