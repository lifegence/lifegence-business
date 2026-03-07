# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import today


@frappe.whitelist()
def create_finding(audit_engagement, finding_title, severity, category, description, recommendation):
	"""Create a new audit finding."""
	try:
		doc = frappe.get_doc({
			"doctype": "Audit Finding",
			"audit_engagement": audit_engagement,
			"finding_title": finding_title,
			"severity": severity,
			"category": category,
			"description": description,
			"recommendation": recommendation,
			"finding_date": today(),
			"reported_by": frappe.session.user,
		})
		doc.insert(ignore_permissions=True)
		return {
			"success": True,
			"data": {"finding": doc.name, "status": doc.status},
		}
	except Exception as e:
		frappe.log_error(f"create_finding error: {e}")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_findings(audit_engagement=None, severity=None, category=None, status=None, limit=20, offset=0):
	"""Get list of audit findings with filters."""
	try:
		filters = {}
		if audit_engagement:
			filters["audit_engagement"] = audit_engagement
		if severity:
			filters["severity"] = severity
		if category:
			filters["category"] = category
		if status:
			filters["status"] = status

		findings = frappe.get_all(
			"Audit Finding",
			filters=filters,
			fields=[
				"name", "finding_title", "audit_engagement", "severity",
				"category", "status", "finding_date", "reported_by",
			],
			order_by="finding_date desc",
			limit_page_length=int(limit),
			limit_start=int(offset),
		)
		total = frappe.db.count("Audit Finding", filters)

		return {
			"success": True,
			"data": {"findings": findings, "total": total},
		}
	except Exception as e:
		frappe.log_error(f"get_findings error: {e}")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_finding_detail(finding_name):
	"""Get detailed information about a finding."""
	try:
		finding = frappe.get_doc("Audit Finding", finding_name)

		corrective_actions = frappe.get_all(
			"Corrective Action",
			filters={"audit_finding": finding_name},
			fields=["name", "action_title", "status", "due_date", "responsible_person"],
		)

		return {
			"success": True,
			"data": {
				"finding": {
					"name": finding.name,
					"finding_title": finding.finding_title,
					"severity": finding.severity,
					"category": finding.category,
					"status": finding.status,
					"description": finding.description,
					"root_cause": finding.root_cause,
					"recommendation": finding.recommendation,
					"management_response": finding.management_response,
				},
				"corrective_actions": corrective_actions,
			},
		}
	except Exception as e:
		frappe.log_error(f"get_finding_detail error: {e}")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def update_finding_status(finding_name, status, comments=None):
	"""Update a finding's status."""
	try:
		doc = frappe.get_doc("Audit Finding", finding_name)
		doc.status = status
		if comments:
			doc.add_comment("Comment", comments)
		doc.save(ignore_permissions=True)

		return {
			"success": True,
			"data": {"finding": doc.name, "new_status": doc.status},
		}
	except Exception as e:
		frappe.log_error(f"update_finding_status error: {e}")
		return {"success": False, "error": str(e)}
