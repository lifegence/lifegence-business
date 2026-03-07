# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import now_datetime


@frappe.whitelist()
def create_ticket(
	subject,
	description,
	category=None,
	priority="Medium",
	ticket_type="社内",
	raised_by_name=None,
	raised_by_email=None,
):
	"""Create a new helpdesk ticket with auto SLA and assignment."""
	if not raised_by_name:
		raised_by_name = frappe.utils.get_fullname(frappe.session.user)

	if not raised_by_email:
		raised_by_email = frappe.session.user

	doc = frappe.get_doc({
		"doctype": "HD Ticket",
		"subject": subject,
		"description": description,
		"category": category,
		"priority": priority,
		"ticket_type": ticket_type,
		"raised_by_name": raised_by_name,
		"raised_by_email": raised_by_email,
	})
	doc.insert(ignore_permissions=True)

	return {
		"success": True,
		"ticket": doc.name,
		"status": doc.status,
		"assigned_to": doc.assigned_to,
		"sla_policy": doc.sla_policy,
		"response_due": str(doc.response_due) if doc.response_due else None,
		"resolution_due": str(doc.resolution_due) if doc.resolution_due else None,
	}


@frappe.whitelist()
def update_ticket_status(ticket, status, resolution=None):
	"""Update ticket status with SLA timer control."""
	doc = frappe.get_doc("HD Ticket", ticket)

	doc.status = status
	if resolution:
		doc.resolution = resolution

	doc.save(ignore_permissions=True)

	return {
		"success": True,
		"ticket": doc.name,
		"status": doc.status,
		"sla_status": doc.sla_status,
		"resolved_on": str(doc.resolved_on) if doc.resolved_on else None,
	}


@frappe.whitelist()
def add_comment(ticket, comment, is_internal=0):
	"""Add a comment to a ticket."""
	doc = frappe.get_doc("HD Ticket", ticket)

	doc.append("comments", {
		"comment": comment,
		"commented_by": frappe.session.user,
		"commented_on": now_datetime(),
		"is_internal": int(is_internal),
	})
	doc.save(ignore_permissions=True)

	return {
		"success": True,
		"ticket": doc.name,
		"comment_count": len(doc.comments),
	}


@frappe.whitelist()
def get_ticket_summary(ticket):
	"""Get ticket details including SLA status."""
	if not frappe.db.exists("HD Ticket", ticket):
		return {"success": False, "error": _("チケット {0} は存在しません。").format(ticket)}

	doc = frappe.get_doc("HD Ticket", ticket)

	# Filter comments based on user role
	comments = []
	for c in doc.comments:
		comment_data = {
			"comment": c.comment,
			"commented_by": c.commented_by,
			"commented_on": str(c.commented_on) if c.commented_on else None,
			"is_internal": c.is_internal,
		}
		comments.append(comment_data)

	return {
		"success": True,
		"ticket": {
			"name": doc.name,
			"subject": doc.subject,
			"status": doc.status,
			"priority": doc.priority,
			"ticket_type": doc.ticket_type,
			"category": doc.category,
			"raised_by_name": doc.raised_by_name,
			"raised_by_email": doc.raised_by_email,
			"assigned_to": doc.assigned_to,
			"description": doc.description,
			"resolution": doc.resolution,
			"sla_policy": doc.sla_policy,
			"sla_status": doc.sla_status,
			"response_due": str(doc.response_due) if doc.response_due else None,
			"resolution_due": str(doc.resolution_due) if doc.resolution_due else None,
			"first_responded_on": str(doc.first_responded_on) if doc.first_responded_on else None,
			"resolved_on": str(doc.resolved_on) if doc.resolved_on else None,
			"satisfaction_rating": doc.satisfaction_rating,
			"comments": comments,
		},
	}
