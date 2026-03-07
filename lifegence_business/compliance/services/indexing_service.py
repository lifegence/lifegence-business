# Copyright (c) 2025, Lifegence and contributors
# For license information, please see license.txt

import time
import uuid

import frappe
from frappe.utils import now_datetime

from lifegence_business.compliance.services import (
	embedding_service,
	pdf_service,
	qdrant_service,
)


def _log_operation(report_name, operation, status, message="", duration=0.0):
	"""Create an indexing log entry."""
	frappe.get_doc({
		"doctype": "Indexing Log",
		"report": report_name,
		"operation": operation,
		"status": status,
		"message": message[:500] if message else "",
		"duration_seconds": duration,
	}).insert(ignore_permissions=True)


def index_report(report_name, file_path=None):
	"""
	Full indexing pipeline for a single report:
	1. Extract text from PDF
	2. Chunk the text
	3. Generate embeddings
	4. Store chunks in DB
	5. Upsert vectors to Qdrant

	Args:
		report_name: Committee Report document name
		file_path: optional override for PDF file path

	Returns:
		dict with indexing results
	"""
	doc = frappe.get_doc("Committee Report", report_name)

	if not file_path:
		# Determine file path from settings base path + year + files + filename
		settings = frappe.get_single("Compliance Settings")
		base_path = settings.reports_base_path
		file_path = f"{base_path}/{doc.year}/files/{doc.filename}"

	start_time = time.time()
	doc.indexing_status = "Processing"
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	try:
		# Step 1: Extract text
		_log_operation(report_name, "Extract Text", "Started")
		t0 = time.time()
		result = pdf_service.extract_text(file_path)
		text = result["text"]
		page_count = result["page_count"]
		_log_operation(
			report_name, "Extract Text", "Success",
			f"Extracted {len(text)} chars, {page_count} pages",
			time.time() - t0,
		)

		if not text.strip():
			raise ValueError("No text extracted from PDF")

		doc.total_pages = page_count

		# Step 2: Chunk the text
		_log_operation(report_name, "Chunk", "Started")
		t0 = time.time()
		chunks = embedding_service.chunk_text(text)
		_log_operation(
			report_name, "Chunk", "Success",
			f"Created {len(chunks)} chunks",
			time.time() - t0,
		)

		if not chunks:
			raise ValueError("No chunks created from text")

		# Step 3: Generate embeddings
		_log_operation(report_name, "Embed", "Started")
		t0 = time.time()
		chunk_texts = [c["content"] for c in chunks]
		embeddings = embedding_service.generate_batch(chunk_texts)
		_log_operation(
			report_name, "Embed", "Success",
			f"Generated {len(embeddings)} embeddings",
			time.time() - t0,
		)

		# Step 4: Store chunks in DB
		# Delete existing chunks first
		frappe.db.delete("Report Chunk", {"report": report_name})

		for i, chunk in enumerate(chunks):
			has_embedding = embeddings[i] and any(v != 0.0 for v in embeddings[i])
			frappe.get_doc({
				"doctype": "Report Chunk",
				"report": report_name,
				"chunk_index": chunk["index"],
				"content": chunk["content"],
				"metadata": frappe.as_json({
					"offset": chunk["offset"],
					"length": chunk["length"],
				}),
				"has_embedding": 1 if has_embedding else 0,
			}).insert(ignore_permissions=True)

		# Step 5: Upsert to Qdrant
		_log_operation(report_name, "Index", "Started")
		t0 = time.time()
		qdrant_service.ensure_collection()

		# Delete existing vectors for this report
		qdrant_service.delete_report_vectors(report_name)

		# Build points
		points = []
		for i, chunk in enumerate(chunks):
			if embeddings[i] and any(v != 0.0 for v in embeddings[i]):
				point_id = str(uuid.uuid4())
				points.append({
					"id": point_id,
					"vector": embeddings[i],
					"payload": {
						"report_name": report_name,
						"chunk_index": chunk["index"],
						"content": chunk["content"],
						"company_name": doc.company_name or "",
						"company_code": doc.company_code or "",
						"year": doc.year,
						"market": doc.market or "",
					},
				})

		if points:
			qdrant_service.upsert_vectors(points)

		_log_operation(
			report_name, "Index", "Success",
			f"Indexed {len(points)} vectors",
			time.time() - t0,
		)

		# Update report
		total_duration = time.time() - start_time
		doc.indexing_status = "Indexed"
		doc.chunk_count = len(chunks)
		doc.indexed_at = now_datetime()
		doc.save(ignore_permissions=True)
		frappe.db.commit()

		return {
			"report_name": report_name,
			"status": "success",
			"chunks": len(chunks),
			"vectors": len(points),
			"pages": page_count,
			"duration": round(total_duration, 2),
		}

	except Exception as e:
		_log_operation(report_name, "Index", "Failed", str(e))
		doc.reload()
		doc.indexing_status = "Failed"
		doc.save(ignore_permissions=True)
		frappe.db.commit()
		raise


def index_all_pending(limit=None):
	"""
	Index all reports with status 'Pending'.

	Args:
		limit: max number of reports to process

	Returns:
		dict with batch results
	"""
	filters = {"indexing_status": "Pending"}
	reports = frappe.get_all(
		"Committee Report",
		filters=filters,
		fields=["name", "filename", "year"],
		order_by="year desc, creation desc",
		limit_page_length=limit or 0,
	)

	results = {"indexed": 0, "failed": 0, "errors": []}

	for report in reports:
		try:
			index_report(report.name)
			results["indexed"] += 1
			print(f"  Indexed: {report.name} ({report.filename})")
		except Exception as e:
			results["failed"] += 1
			results["errors"].append({
				"report": report.name,
				"filename": report.filename,
				"error": str(e),
			})
			print(f"  Failed: {report.name} - {e}")

	return results


def reindex_report(report_name):
	"""Force reindex a report regardless of current status."""
	doc = frappe.get_doc("Committee Report", report_name)
	doc.indexing_status = "Pending"
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return index_report(report_name)
