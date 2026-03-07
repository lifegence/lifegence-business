# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe import _


@frappe.whitelist()
def get_helpdesk_dashboard(company=None):
	"""Get helpdesk dashboard summary with ticket counts and SLA compliance."""
	filters = {}
	if company:
		filters["company"] = company

	# Ticket counts by status
	status_counts = {}
	for status in ("Open", "In Progress", "Waiting for Customer", "Resolved", "Closed"):
		status_filters = {**filters, "status": status}
		status_counts[status] = frappe.db.count("HD Ticket", status_filters)

	# SLA compliance
	total_with_sla = frappe.db.count(
		"HD Ticket",
		{**filters, "sla_policy": ["is", "set"]},
	)
	breached = frappe.db.count(
		"HD Ticket",
		{**filters, "sla_status": "Breached"},
	)
	compliance_rate = (
		round((total_with_sla - breached) / total_with_sla * 100, 1)
		if total_with_sla > 0
		else 100.0
	)

	# Category breakdown
	category_counts = frappe.db.sql(
		"""
		SELECT category, COUNT(*) as count
		FROM `tabHD Ticket`
		WHERE status NOT IN ('Closed')
		{company_filter}
		GROUP BY category
		ORDER BY count DESC
		""".format(
			company_filter=f"AND company = {frappe.db.escape(company)}" if company else ""
		),
		as_dict=True,
	)

	# Priority breakdown (active tickets only)
	priority_counts = frappe.db.sql(
		"""
		SELECT priority, COUNT(*) as count
		FROM `tabHD Ticket`
		WHERE status NOT IN ('Resolved', 'Closed')
		{company_filter}
		GROUP BY priority
		ORDER BY FIELD(priority, 'Urgent', 'High', 'Medium', 'Low')
		""".format(
			company_filter=f"AND company = {frappe.db.escape(company)}" if company else ""
		),
		as_dict=True,
	)

	return {
		"success": True,
		"status_counts": status_counts,
		"sla": {
			"total_with_sla": total_with_sla,
			"breached": breached,
			"compliance_rate": compliance_rate,
		},
		"by_category": category_counts,
		"by_priority": priority_counts,
	}
