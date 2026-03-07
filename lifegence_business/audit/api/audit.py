# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe


@frappe.whitelist()
def get_audit_dashboard(fiscal_year=None):
	"""Get comprehensive audit dashboard data."""
	try:
		from lifegence_business.audit.services.audit_service import get_audit_plan_summary, get_findings_summary
		from lifegence_business.audit.services.corrective_action_service import get_overdue_actions_data
		from lifegence_business.audit.services.risk_service import get_risk_summary_data

		plan_summary = get_audit_plan_summary(fiscal_year)
		findings_summary = get_findings_summary(fiscal_year)

		# Corrective actions summary
		all_actions = frappe.get_all(
			"Corrective Action",
			fields=["status"],
		)
		ca_summary = {
			"total": len(all_actions),
			"completed": sum(1 for a in all_actions if a.status == "Completed"),
			"in_progress": sum(1 for a in all_actions if a.status == "In Progress"),
			"overdue": sum(1 for a in all_actions if a.status == "Overdue"),
			"open": sum(1 for a in all_actions if a.status == "Open"),
			"overdue_details": get_overdue_actions_data(),
		}

		risk_summary = get_risk_summary_data()

		return {
			"success": True,
			"data": {
				"plan_summary": plan_summary,
				"findings_summary": findings_summary,
				"corrective_actions_summary": ca_summary,
				"risk_summary": risk_summary,
			},
		}
	except Exception as e:
		frappe.log_error(f"get_audit_dashboard error: {e}")
		return {"success": False, "error": str(e)}
