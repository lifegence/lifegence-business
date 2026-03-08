# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe


def on_checklist_item_update(doc, method=None):
	"""Recalculate checklist summary when an item result changes."""
	if doc.parenttype != "Audit Checklist":
		return
	parent = frappe.get_doc("Audit Checklist", doc.parent)
	parent.update_summary()
	parent.save(ignore_permissions=True)


def get_audit_plan_summary(fiscal_year=None):
	"""Get summary of audit plans for dashboard."""
	filters = {}
	if fiscal_year:
		filters["fiscal_year"] = fiscal_year

	plans = frappe.get_all(
		"Audit Plan",
		filters=filters,
		fields=["name", "status", "planned_audits", "completed_audits", "total_findings", "critical_findings"],
	)

	engagements = frappe.get_all(
		"Audit Engagement",
		filters={"audit_plan": ["in", [p.name for p in plans] or [""]]},
		fields=["status"],
	)

	return {
		"total_plans": len(plans),
		"total_engagements": len(engagements),
		"completed": sum(1 for e in engagements if e.status == "Closed"),
		"in_progress": sum(1 for e in engagements if e.status in ("Fieldwork", "Reporting", "Review")),
		"planned": sum(1 for e in engagements if e.status == "Planning"),
		"completion_rate": round(
			sum(1 for e in engagements if e.status == "Closed") / len(engagements) * 100, 1
		) if engagements else 0,
	}


def get_findings_summary(fiscal_year=None):
	"""Get summary of audit findings."""
	filters = {}
	if fiscal_year:
		plans = frappe.get_all("Audit Plan", filters={"fiscal_year": fiscal_year}, pluck="name")
		engagements = frappe.get_all(
			"Audit Engagement",
			filters={"audit_plan": ["in", plans or [""]]},
			pluck="name",
		)
		filters["audit_engagement"] = ["in", engagements or [""]]

	findings = frappe.get_all(
		"Audit Finding",
		filters=filters,
		fields=["severity", "status"],
	)

	by_severity = {}
	by_status = {}
	for f in findings:
		by_severity[f.severity] = by_severity.get(f.severity, 0) + 1
		by_status[f.status] = by_status.get(f.status, 0) + 1

	return {
		"total": len(findings),
		"by_severity": by_severity,
		"by_status": by_status,
	}
