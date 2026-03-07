# Copyright (c) 2025, Lifegence and contributors
# For license information, please see license.txt

import frappe


@frappe.whitelist()
def index_report(report_name=None):
	"""Index a single report (extract, chunk, embed, store in Qdrant)."""
	if not report_name:
		frappe.throw("report_name parameter is required")

	from lifegence_compliance.services.indexing_service import index_report as _index_report
	return _index_report(report_name)


@frappe.whitelist()
def index_batch(limit=10):
	"""Index a batch of pending reports."""
	from lifegence_compliance.services.indexing_service import index_all_pending
	return index_all_pending(limit=int(limit))


@frappe.whitelist()
def reindex_report(report_name=None):
	"""Force reindex a report."""
	if not report_name:
		frappe.throw("report_name parameter is required")

	from lifegence_compliance.services.indexing_service import reindex_report as _reindex_report
	return _reindex_report(report_name)
