# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import add_days, today


def send_due_reminders():
	"""Daily scheduler: send reminders for corrective actions approaching due date."""
	settings = frappe.get_single("Audit Settings")
	reminder_days = settings.auto_reminder_days or 7

	upcoming = frappe.get_all(
		"Corrective Action",
		filters={
			"status": ["in", ["Open", "In Progress"]],
			"due_date": ["between", [today(), add_days(today(), reminder_days)]],
		},
		fields=["name", "action_title", "due_date", "responsible_person"],
	)

	for action in upcoming:
		if not action.responsible_person:
			continue
		frappe.sendmail(
			recipients=[action.responsible_person],
			subject=f"是正措置期限リマインダー: {action.action_title}",
			message=(
				f"是正措置「{action.action_title}」({action.name})の対応期限が"
				f"{action.due_date}に迫っています。対応状況をご確認ください。"
			),
		)
