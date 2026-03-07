# Copyright (c) 2025, Lifegence and contributors
# For license information, please see license.txt

import frappe


@frappe.whitelist()
def get_reports(page=1, limit=50, year=None, company_name=None,
				indexing_status=None, classification_status=None):
	"""Get paginated list of committee reports."""
	page = int(page)
	limit = int(limit)
	offset = (page - 1) * limit

	filters = {}
	if year:
		filters["year"] = int(year)
	if company_name:
		filters["company_name"] = ["like", f"%{company_name}%"]
	if indexing_status:
		filters["indexing_status"] = indexing_status
	if classification_status:
		filters["classification_status"] = classification_status

	total = frappe.db.count("Committee Report", filters)

	reports = frappe.get_all(
		"Committee Report",
		filters=filters,
		fields=[
			"name", "filename", "year", "company_name", "company_code",
			"market", "indexing_status", "classification_status",
			"chunk_count", "creation",
		],
		order_by="year desc, company_name asc",
		start=offset,
		limit_page_length=limit,
	)

	return {
		"data": reports,
		"pagination": {
			"page": page,
			"limit": limit,
			"total": total,
			"total_pages": (total + limit - 1) // limit,
		},
	}


@frappe.whitelist()
def get_report(report_name=None):
	"""Get detailed information for a single report."""
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
		"name": doc.name,
		"filename": doc.filename,
		"source_url": doc.source_url,
		"year": doc.year,
		"company_name": doc.company_name,
		"company_code": doc.company_code,
		"market": doc.market,
		"auditor": doc.auditor,
		"committee_members": doc.committee_members,
		"purpose": doc.purpose,
		"total_pages": doc.total_pages,
		"report_date": doc.report_date,
		"indexing_status": doc.indexing_status,
		"classification_status": doc.classification_status,
		"chunk_count": doc.chunk_count,
		"indexed_at": doc.indexed_at,
		"classified_at": doc.classified_at,
		"classifications": classifications,
		"ai_summary": doc.ai_summary,
	}


@frappe.whitelist()
def get_stats():
	"""Get system-wide statistics."""
	total = frappe.db.count("Committee Report")
	indexed = frappe.db.count("Committee Report", {"indexing_status": "Indexed"})
	classified = frappe.db.count("Committee Report", {"classification_status": "Classified"})
	chunks = frappe.db.count("Report Chunk")

	years = frappe.db.sql(
		"SELECT DISTINCT year FROM `tabCommittee Report` ORDER BY year DESC",
		as_list=True,
	)
	year_list = [y[0] for y in years] if years else []

	companies = frappe.db.sql(
		"SELECT COUNT(DISTINCT company_name) FROM `tabCommittee Report`",
		as_list=True,
	)
	unique_companies = companies[0][0] if companies else 0

	return {
		"total_reports": total,
		"indexed_reports": indexed,
		"classified_reports": classified,
		"total_chunks": chunks,
		"unique_companies": unique_companies,
		"earliest_year": min(year_list) if year_list else None,
		"latest_year": max(year_list) if year_list else None,
	}


@frappe.whitelist()
def get_years():
	"""Get list of available years."""
	years = frappe.db.sql(
		"SELECT DISTINCT year FROM `tabCommittee Report` ORDER BY year DESC",
		as_list=True,
	)
	return [y[0] for y in years] if years else []


@frappe.whitelist()
def get_companies(year=None):
	"""Get list of company names, optionally filtered by year."""
	filters = {}
	if year:
		filters["year"] = int(year)

	companies = frappe.get_all(
		"Committee Report",
		filters=filters,
		fields=["company_name"],
		distinct=True,
		order_by="company_name asc",
	)

	return [c["company_name"] for c in companies]


@frappe.whitelist()
def get_report_chunks(report_name=None, limit=100):
	"""Get chunks for a specific report."""
	if not report_name:
		frappe.throw("report_name parameter is required")

	chunks = frappe.get_all(
		"Report Chunk",
		filters={"report": report_name},
		fields=["name", "chunk_index", "content", "has_embedding", "metadata"],
		order_by="chunk_index asc",
		limit_page_length=int(limit),
	)

	return chunks
