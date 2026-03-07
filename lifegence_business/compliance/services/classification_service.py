# Copyright (c) 2025, Lifegence and contributors
# For license information, please see license.txt

import json
import time

import frappe
import google.generativeai as genai
from frappe.utils import now_datetime

from lifegence_business.compliance.classification.prompts import (
	get_analysis_prompt,
	get_chunk_analysis_prompt,
	get_system_prompt,
)
from lifegence_business.compliance.classification.taxonomy import get_category


def _configure_genai():
	"""Configure the Gemini API client and return settings."""
	from lifegence_business.compliance.compliance.doctype.compliance_settings.compliance_settings import ComplianceSettings
	settings = frappe.get_single("Compliance Settings")
	api_key = ComplianceSettings.get_gemini_api_key()
	if not api_key:
		frappe.throw("Gemini API Key is not configured in Compliance Settings or Company OS AI Settings")
	genai.configure(api_key=api_key)
	return settings


def _call_gemini(system_prompt, user_prompt, settings):
	"""Call Gemini API and return parsed JSON response."""
	model_name = settings.classification_model or "gemini-2.0-flash"

	model = genai.GenerativeModel(
		model_name=model_name,
		system_instruction=system_prompt,
		generation_config=genai.GenerationConfig(
			temperature=0.3,
			top_p=0.8,
			max_output_tokens=4096,
		),
	)

	response = model.generate_content(user_prompt)
	text = response.text.strip()

	# Extract JSON from response (handle markdown code blocks)
	if text.startswith("```"):
		# Remove markdown code block
		lines = text.split("\n")
		text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
		text = text.strip()

	return json.loads(text)


def classify_report(report_name, force_reclassify=False):
	"""
	Classify a committee report using AI analysis.

	Strategy:
	1. Select key chunks (first, middle, last) for efficiency
	2. Analyze each chunk individually
	3. Aggregate results to report level
	4. Store classifications in the child table

	Args:
		report_name: Committee Report document name
		force_reclassify: if True, reclassify even if already classified

	Returns:
		dict with classification results
	"""
	doc = frappe.get_doc("Committee Report", report_name)

	if doc.classification_status == "Classified" and not force_reclassify:
		return {"status": "already_classified", "report_name": report_name}

	settings = _configure_genai()
	system_prompt = get_system_prompt()

	doc.classification_status = "Processing"
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	try:
		# Get chunks for this report
		chunks = frappe.get_all(
			"Report Chunk",
			filters={"report": report_name},
			fields=["name", "chunk_index", "content"],
			order_by="chunk_index asc",
		)

		if not chunks:
			raise ValueError("No chunks found for this report. Index the report first.")

		# Select key chunks (strategy: first, middle, last + a few others)
		selected = _select_key_chunks(chunks, max_chunks=5)

		# Analyze chunks
		all_results = []
		for chunk in selected:
			try:
				prompt = get_chunk_analysis_prompt(chunk["content"])
				result = _call_gemini(system_prompt, prompt, settings)
				all_results.append(result)
				time.sleep(0.5)  # Rate limiting
			except Exception as e:
				frappe.logger().warning(
					f"Chunk analysis failed for {report_name} chunk {chunk['chunk_index']}: {e}"
				)

		if not all_results:
			raise ValueError("All chunk analyses failed")

		# Also do a full-report analysis using the first and last chunks combined
		combined_text = "\n\n".join([
			chunks[0]["content"],
			chunks[-1]["content"] if len(chunks) > 1 else "",
		])
		try:
			full_prompt = get_analysis_prompt(combined_text)
			full_result = _call_gemini(system_prompt, full_prompt, settings)
			all_results.append(full_result)
		except Exception as e:
			frappe.logger().warning(f"Full report analysis failed: {e}")

		# Aggregate results
		aggregated = _aggregate_classifications(all_results)

		# Store classifications
		doc.reload()
		doc.classifications = []

		for item in aggregated["classifications"]:
			doc.append("classifications", {
				"layer": item["layer"],
				"category_code": item["code"],
				"category_name": item["name"],
				"confidence": item["confidence"],
				"evidence": item.get("evidence", ""),
			})

		# Store summary
		summary = aggregated.get("summary", "")
		if summary:
			doc.ai_summary = summary

		doc.classification_status = "Classified"
		doc.classified_at = now_datetime()
		doc.save(ignore_permissions=True)
		frappe.db.commit()

		# Update Qdrant payload with classifications
		_update_qdrant_classifications(report_name, aggregated["classifications"])

		return {
			"status": "success",
			"report_name": report_name,
			"classifications": aggregated["classifications"],
			"summary": summary,
		}

	except Exception as e:
		doc.reload()
		doc.classification_status = "Failed"
		doc.save(ignore_permissions=True)
		frappe.db.commit()
		raise


def classify_text(text):
	"""
	Classify arbitrary text (not tied to a report).

	Args:
		text: text to classify

	Returns:
		dict with classification results
	"""
	settings = _configure_genai()
	system_prompt = get_system_prompt()
	prompt = get_analysis_prompt(text)
	result = _call_gemini(system_prompt, prompt, settings)
	return _normalize_classification_result(result)


def classify_all_pending(limit=None):
	"""
	Classify all reports with status 'Pending' that are already indexed.

	Args:
		limit: max number of reports to classify

	Returns:
		dict with batch results
	"""
	reports = frappe.get_all(
		"Committee Report",
		filters={
			"classification_status": "Pending",
			"indexing_status": "Indexed",
		},
		fields=["name", "filename", "company_name"],
		order_by="year desc, creation desc",
		limit_page_length=limit or 0,
	)

	results = {"classified": 0, "failed": 0, "errors": []}

	for report in reports:
		try:
			classify_report(report.name)
			results["classified"] += 1
			print(f"  Classified: {report.name} ({report.company_name})")
		except Exception as e:
			results["failed"] += 1
			results["errors"].append({
				"report": report.name,
				"error": str(e),
			})
			print(f"  Failed: {report.name} - {e}")

	return results


def _select_key_chunks(chunks, max_chunks=5):
	"""Select strategically important chunks for analysis."""
	if len(chunks) <= max_chunks:
		return chunks

	selected_indices = set()

	# Always include first and last
	selected_indices.add(0)
	selected_indices.add(len(chunks) - 1)

	# Include middle
	mid = len(chunks) // 2
	selected_indices.add(mid)

	# Include quarter points
	q1 = len(chunks) // 4
	q3 = 3 * len(chunks) // 4
	selected_indices.add(q1)
	selected_indices.add(q3)

	# Sort and limit
	indices = sorted(selected_indices)[:max_chunks]
	return [chunks[i] for i in indices]


def _aggregate_classifications(results):
	"""Aggregate multiple chunk classification results into a single report-level result."""
	category_scores = {}  # code -> {total_confidence, count, evidences}
	summary = ""

	for result in results:
		for layer_key in ["layer_a", "layer_b", "layer_c"]:
			items = result.get(layer_key, [])
			for item in items:
				code = item.get("code", "")
				if not code:
					continue

				if code not in category_scores:
					category_scores[code] = {
						"total_confidence": 0.0,
						"count": 0,
						"evidences": [],
					}

				confidence = float(item.get("confidence", 0.5))
				category_scores[code]["total_confidence"] += confidence
				category_scores[code]["count"] += 1

				evidence = item.get("evidence", "")
				if evidence and evidence not in category_scores[code]["evidences"]:
					category_scores[code]["evidences"].append(evidence)

		# Use the last summary found
		if result.get("summary"):
			summary = result["summary"]

	# Build final classification list
	classifications = []
	for code, scores in category_scores.items():
		avg_confidence = scores["total_confidence"] / scores["count"]

		# Only include categories with reasonable confidence
		if avg_confidence < 0.3:
			continue

		cat_info = get_category(code)
		if not cat_info:
			continue

		layer = code[0]
		classifications.append({
			"layer": layer,
			"code": code,
			"name": cat_info["name"],
			"confidence": round(avg_confidence, 2),
			"evidence": "; ".join(scores["evidences"][:3]),
		})

	# Sort by layer then confidence
	classifications.sort(key=lambda x: (x["layer"], -x["confidence"]))

	return {
		"classifications": classifications,
		"summary": summary,
	}


def _normalize_classification_result(result):
	"""Normalize a single classification result."""
	classifications = []

	for layer_key in ["layer_a", "layer_b", "layer_c"]:
		items = result.get(layer_key, [])
		for item in items:
			code = item.get("code", "")
			cat_info = get_category(code)
			if cat_info:
				classifications.append({
					"layer": code[0],
					"code": code,
					"name": cat_info["name"],
					"confidence": float(item.get("confidence", 0.5)),
					"evidence": item.get("evidence", ""),
				})

	return {
		"classifications": classifications,
		"summary": result.get("summary", ""),
	}


def _update_qdrant_classifications(report_name, classifications):
	"""Update Qdrant point payloads with classification codes."""
	try:
		from lifegence_business.compliance.services.qdrant_service import get_client, get_collection_name
		from qdrant_client.models import Filter, FieldCondition, MatchValue

		client = get_client()
		collection_name = get_collection_name()
		codes = [c["code"] for c in classifications]

		# Find points for this report
		results = client.scroll(
			collection_name=collection_name,
			scroll_filter=Filter(
				must=[FieldCondition(key="report_name", match=MatchValue(value=report_name))]
			),
			limit=1000,
		)

		points = results[0]
		if not points:
			return

		# Update each point's payload
		point_ids = [p.id for p in points]
		client.set_payload(
			collection_name=collection_name,
			payload={"classifications": codes},
			points=point_ids,
		)

	except Exception as e:
		frappe.logger().warning(f"Failed to update Qdrant classifications for {report_name}: {e}")
