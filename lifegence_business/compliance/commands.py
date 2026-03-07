# Copyright (c) 2025, Lifegence and contributors
# For license information, please see license.txt

import click
import frappe
from frappe.commands import get_site, pass_context


@click.command("compliance-import")
@click.option("--base-path", default=None, help="Base path to downloaded reports")
@pass_context
def compliance_import(context, base_path=None):
	"""Import committee reports from downloaded PDF files."""
	site = get_site(context)
	frappe.init(site=site)
	frappe.connect()

	try:
		from lifegence_business.compliance.services.scraper_service import import_from_downloaded

		print(f"Importing reports from: {base_path or 'Compliance Settings path'}")
		result = import_from_downloaded(base_path)
		print(f"Registered: {result['registered']}")
		print(f"Skipped (duplicates): {result['skipped']}")
		if result["errors"]:
			print(f"Errors: {len(result['errors'])}")
			for err in result["errors"][:10]:
				print(f"  - {err['filename']}: {err['error']}")
	finally:
		frappe.destroy()


@click.command("compliance-index")
@click.option("--limit", default=None, type=int, help="Max reports to index")
@click.option("--report", default=None, help="Specific report name to index")
@pass_context
def compliance_index(context, limit=None, report=None):
	"""Index committee reports (PDF extraction + embedding + Qdrant)."""
	site = get_site(context)
	frappe.init(site=site)
	frappe.connect()

	try:
		from lifegence_business.compliance.services.indexing_service import (
			index_all_pending,
			index_report,
		)

		if report:
			print(f"Indexing report: {report}")
			result = index_report(report)
			print(f"  Chunks: {result['chunks']}, Vectors: {result['vectors']}, "
				  f"Duration: {result['duration']}s")
		else:
			print(f"Indexing pending reports (limit: {limit or 'all'})")
			result = index_all_pending(limit)
			print(f"Indexed: {result['indexed']}")
			print(f"Failed: {result['failed']}")
			if result["errors"]:
				for err in result["errors"][:10]:
					print(f"  - {err['report']}: {err['error']}")
	finally:
		frappe.destroy()


@click.command("compliance-classify")
@click.option("--limit", default=None, type=int, help="Max reports to classify")
@click.option("--report", default=None, help="Specific report name to classify")
@click.option("--force", is_flag=True, help="Force reclassification")
@pass_context
def compliance_classify(context, limit=None, report=None, force=False):
	"""Classify committee reports using AI."""
	site = get_site(context)
	frappe.init(site=site)
	frappe.connect()

	try:
		from lifegence_business.compliance.services.classification_service import (
			classify_all_pending,
			classify_report,
		)

		if report:
			print(f"Classifying report: {report}")
			result = classify_report(report, force_reclassify=force)
			print(f"  Classifications: {len(result.get('classifications', []))}")
		else:
			print(f"Classifying pending reports (limit: {limit or 'all'})")
			result = classify_all_pending(limit)
			print(f"Classified: {result['classified']}")
			print(f"Failed: {result['failed']}")
	finally:
		frappe.destroy()


@click.command("compliance-stats")
@pass_context
def compliance_stats(context):
	"""Show compliance system statistics."""
	site = get_site(context)
	frappe.init(site=site)
	frappe.connect()

	try:
		total = frappe.db.count("Committee Report")
		indexed = frappe.db.count("Committee Report", {"indexing_status": "Indexed"})
		classified = frappe.db.count("Committee Report", {"classification_status": "Classified"})
		failed_idx = frappe.db.count("Committee Report", {"indexing_status": "Failed"})
		failed_cls = frappe.db.count("Committee Report", {"classification_status": "Failed"})
		chunks = frappe.db.count("Report Chunk")
		categories = frappe.db.count("Classification Category")

		print("=== Compliance System Statistics ===")
		print(f"Total Reports:      {total}")
		print(f"Indexed:            {indexed}")
		print(f"Classified:         {classified}")
		print(f"Failed (Index):     {failed_idx}")
		print(f"Failed (Classify):  {failed_cls}")
		print(f"Total Chunks:       {chunks}")
		print(f"Categories:         {categories}")

		# Qdrant info
		try:
			from lifegence_business.compliance.services.qdrant_service import get_collection_info
			info = get_collection_info()
			print(f"\n=== Qdrant ===")
			print(f"Collection:         {info['name']}")
			print(f"Points:             {info['points_count']}")
			print(f"Status:             {info['status']}")
		except Exception as e:
			print(f"\nQdrant: Not available ({e})")

		# Year breakdown
		years = frappe.db.sql(
			"SELECT year, COUNT(*) as cnt FROM `tabCommittee Report` GROUP BY year ORDER BY year DESC",
			as_dict=True,
		)
		if years:
			print(f"\n=== By Year ===")
			for y in years:
				print(f"  {y.year}: {y.cnt} reports")

	finally:
		frappe.destroy()


@click.command("compliance-setup-qdrant")
@pass_context
def compliance_setup_qdrant(context):
	"""Initialize Qdrant collection for committee reports."""
	site = get_site(context)
	frappe.init(site=site)
	frappe.connect()

	try:
		from lifegence_business.compliance.services.qdrant_service import ensure_collection, get_collection_info

		collection = ensure_collection()
		info = get_collection_info()
		print(f"Qdrant collection '{collection}' ready.")
		print(f"  Points: {info['points_count']}")
		print(f"  Status: {info['status']}")
	finally:
		frappe.destroy()


commands = [
	compliance_import,
	compliance_index,
	compliance_classify,
	compliance_stats,
	compliance_setup_qdrant,
]
