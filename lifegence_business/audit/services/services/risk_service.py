# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import add_days, today


def check_risk_review_dates():
	"""Weekly scheduler: check for risks due for review."""
	risks = frappe.get_all(
		"Risk Register",
		filters={
			"status": "Active",
			"review_date": ["<=", today()],
		},
		fields=["name", "risk_title", "risk_owner", "review_date"],
	)

	for risk in risks:
		frappe.sendmail(
			recipients=[risk.risk_owner],
			subject=f"リスク再評価期限到来: {risk.risk_title}",
			message=f"リスク「{risk.risk_title}」({risk.name})の再評価期限が到来しています。リスクアセスメントを実施してください。",
		)


def get_risk_matrix_data(department=None, risk_category=None, jsox_only=False):
	"""Generate risk matrix (heatmap) data."""
	filters = {"status": "Active"}
	if department:
		filters["department"] = department
	if risk_category:
		filters["risk_category"] = risk_category
	if jsox_only:
		filters["jsox_relevant"] = 1

	risks = frappe.get_all(
		"Risk Register",
		filters=filters,
		fields=["name", "risk_title", "likelihood", "impact", "risk_score", "risk_level"],
	)

	cells = []
	for likelihood in range(1, 6):
		for impact in range(1, 6):
			cell_risks = [
				{"name": r.name, "risk_title": r.risk_title}
				for r in risks
				if int(r.likelihood) == likelihood and int(r.impact) == impact
			]
			if cell_risks:
				score = likelihood * impact
				cells.append({
					"likelihood": likelihood,
					"impact": impact,
					"risk_level": _get_risk_level(score),
					"count": len(cell_risks),
					"risks": cell_risks,
				})

	level_dist = {}
	for r in risks:
		level_dist[r.risk_level] = level_dist.get(r.risk_level, 0) + 1

	return {
		"matrix_size": "5x5",
		"cells": cells,
		"total_risks": len(risks),
		"level_distribution": level_dist,
	}


def get_risk_summary_data(department=None, status=None):
	"""Get risk register summary."""
	filters = {}
	if department:
		filters["department"] = department
	if status:
		filters["status"] = status

	risks = frappe.get_all(
		"Risk Register",
		filters=filters,
		fields=["risk_level", "risk_category", "status"],
	)

	by_level = {}
	by_category = {}
	for r in risks:
		by_level[r.risk_level] = by_level.get(r.risk_level, 0) + 1
		by_category[r.risk_category] = by_category.get(r.risk_category, 0) + 1

	review_due = frappe.db.count(
		"Risk Register",
		filters={"status": "Active", "review_date": ["<=", today()]},
	)

	return {
		"total_risks": len(risks),
		"by_level": by_level,
		"by_category": by_category,
		"review_due": review_due,
	}


def _get_risk_level(score):
	if score >= 20:
		return "Critical"
	elif score >= 12:
		return "High"
	elif score >= 6:
		return "Medium"
	else:
		return "Low"
