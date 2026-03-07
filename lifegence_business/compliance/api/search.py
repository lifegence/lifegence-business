# Copyright (c) 2025, Lifegence and contributors
# For license information, please see license.txt

import frappe
from lifegence_compliance.services import search_service


@frappe.whitelist()
def hybrid_search(query=None, limit=None, year=None, company_name=None,
				  classification=None, vector_weight=None, fulltext_weight=None,
				  group_by_report=None):
	"""Perform hybrid vector + full-text search."""
	if not query:
		frappe.throw("query parameter is required")

	return search_service.hybrid_search(
		query=query,
		limit=int(limit) if limit else None,
		year=int(year) if year else None,
		company_name=company_name,
		classification=classification,
		vector_weight=float(vector_weight) if vector_weight else None,
		fulltext_weight=float(fulltext_weight) if fulltext_weight else None,
		group_by_report=group_by_report != "0" if group_by_report is not None else True,
	)


@frappe.whitelist()
def vector_search(query=None, limit=10, year=None, company_name=None,
				  classification=None, group_by_report=None):
	"""Perform vector similarity search."""
	if not query:
		frappe.throw("query parameter is required")

	results = search_service.vector_search(
		query=query,
		limit=int(limit),
		year=int(year) if year else None,
		company_name=company_name,
		classification=classification,
	)

	if group_by_report and group_by_report != "0":
		results["results"] = search_service._group_by_report(results["results"])
		results["grouped"] = True

	return results


@frappe.whitelist()
def fulltext_search(query=None, limit=10, year=None, company_name=None,
					classification=None, group_by_report=None):
	"""Perform full-text search."""
	if not query:
		frappe.throw("query parameter is required")

	results = search_service.fulltext_search(
		query=query,
		limit=int(limit),
		year=int(year) if year else None,
		company_name=company_name,
		classification=classification,
	)

	if group_by_report and group_by_report != "0":
		results["results"] = search_service._group_by_report(results["results"])
		results["grouped"] = True

	return results


@frappe.whitelist()
def find_similar(report_name=None, limit=5):
	"""Find reports similar to a given report."""
	if not report_name:
		frappe.throw("report_name parameter is required")

	return search_service.find_similar(
		report_name=report_name,
		limit=int(limit),
	)
