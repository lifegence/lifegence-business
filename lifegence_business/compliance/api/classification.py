# Copyright (c) 2025, Lifegence and contributors
# For license information, please see license.txt

import frappe
from lifegence_compliance.classification.taxonomy import get_all_categories, get_layer


@frappe.whitelist()
def get_taxonomy():
	"""Get the full classification taxonomy."""
	return {
		"categories": get_all_categories(),
		"layers": {
			"A": {"name": "不正類型", "name_en": "Incident Types", "count": 14},
			"B": {"name": "組織メカニズム", "name_en": "Organizational Mechanisms", "count": 15},
			"C": {"name": "組織文化", "name_en": "Corporate Culture", "count": 10},
		},
	}


@frappe.whitelist()
def get_stats():
	"""Get classification statistics."""
	total = frappe.db.count("Committee Report")
	classified = frappe.db.count("Committee Report", {"classification_status": "Classified"})

	# Category distribution
	distribution = frappe.db.sql("""
		SELECT rc.layer, rc.category_code, rc.category_name, COUNT(*) as count
		FROM `tabReport Classification` rc
		JOIN `tabCommittee Report` cr ON cr.name = rc.parent
		GROUP BY rc.layer, rc.category_code, rc.category_name
		ORDER BY rc.layer, count DESC
	""", as_dict=True)

	return {
		"total_reports": total,
		"classified_reports": classified,
		"pending": total - classified,
		"distribution": distribution,
	}


@frappe.whitelist()
def analyze_text(text=None):
	"""Classify arbitrary text using AI."""
	if not text:
		frappe.throw("Text parameter is required")

	from lifegence_compliance.services.classification_service import classify_text
	return classify_text(text)


@frappe.whitelist()
def get_report_classification(report_name=None):
	"""Get classification results for a specific report."""
	if not report_name:
		frappe.throw("report_name parameter is required")

	doc = frappe.get_doc("Committee Report", report_name)
	classifications = []

	for row in doc.classifications:
		classifications.append({
			"layer": row.layer,
			"category_code": row.category_code,
			"category_name": row.category_name,
			"confidence": row.confidence,
			"evidence": row.evidence,
		})

	return {
		"report_name": report_name,
		"company_name": doc.company_name,
		"year": doc.year,
		"classification_status": doc.classification_status,
		"classifications": classifications,
		"ai_summary": doc.ai_summary,
	}
