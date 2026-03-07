# Copyright (c) 2025, Lifegence and contributors
# For license information, please see license.txt

import re

import frappe

# Regex to detect CJK characters
_CJK_RE = re.compile(r"[\u3000-\u9fff\uf900-\ufaff\uff00-\uffef]")


def hybrid_search(query, limit=None, year=None, company_name=None,
				  classification=None, vector_weight=None, fulltext_weight=None,
				  group_by_report=True):
	"""
	Perform hybrid search combining vector similarity and MariaDB full-text search.

	Args:
		query: search query text
		limit: max results
		year: optional year filter
		company_name: optional company name filter
		classification: optional classification category code filter (e.g. A01, B05)
		vector_weight: weight for vector results (0-1)
		fulltext_weight: weight for full-text results (0-1)
		group_by_report: group results by report (default True)

	Returns:
		dict with results list and metadata
	"""
	settings = frappe.get_single("Compliance Settings")
	limit = limit or int(settings.default_search_limit or 10)
	vector_weight = vector_weight if vector_weight is not None else float(settings.vector_weight or 0.7)
	fulltext_weight = fulltext_weight if fulltext_weight is not None else float(settings.fulltext_weight or 0.3)

	# Get vector results
	vector_results = vector_search(
		query, limit=limit * 2, year=year, company_name=company_name,
		classification=classification,
	)

	# Get full-text results
	fulltext_results = fulltext_search(
		query, limit=limit * 2, year=year, company_name=company_name,
		classification=classification,
	)

	# Merge and score
	scored = {}

	for r in vector_results.get("results", []):
		key = (r["report_name"], r["chunk_index"])
		if key not in scored:
			scored[key] = {**r, "vector_score": 0.0, "fulltext_score": 0.0}
		scored[key]["vector_score"] = r.get("score", 0.0)

	for r in fulltext_results.get("results", []):
		key = (r["report_name"], r["chunk_index"])
		if key not in scored:
			scored[key] = {**r, "vector_score": 0.0, "fulltext_score": 0.0}
		scored[key]["fulltext_score"] = r.get("score", 0.0)

	# Compute hybrid scores
	for key, item in scored.items():
		item["hybrid_score"] = (
			item["vector_score"] * vector_weight +
			item["fulltext_score"] * fulltext_weight
		)

	# Sort by hybrid score
	results = sorted(scored.values(), key=lambda x: x["hybrid_score"], reverse=True)

	# Group by report if requested
	if group_by_report:
		results = _group_by_report(results)

	results = results[:limit]

	return {
		"results": results,
		"count": len(results),
		"query": query,
		"search_type": "hybrid",
		"grouped": group_by_report,
		"params": {
			"vector_weight": vector_weight,
			"fulltext_weight": fulltext_weight,
			"year": year,
			"company_name": company_name,
			"classification": classification,
		},
	}


def vector_search(query, limit=10, year=None, company_name=None, classification=None):
	"""
	Perform vector similarity search using Qdrant.

	Args:
		query: search query text
		limit: max results
		year: optional year filter
		company_name: optional company name filter
		classification: optional classification code filter

	Returns:
		dict with results list
	"""
	# Generate query embedding
	from lifegence_business.compliance.services import embedding_service
	query_embedding = embedding_service.generate_query_embedding(query)

	# Build filters
	filters = {}
	if year:
		filters["year"] = int(year)
	if classification:
		filters["classifications"] = classification

	from lifegence_business.compliance.services import qdrant_service
	qdrant_results = qdrant_service.search_vectors(
		query_vector=query_embedding,
		limit=limit,
		filters=filters if filters else None,
	)

	results = []
	for r in qdrant_results:
		payload = r.get("payload", {})

		# Apply company_name filter client-side (Qdrant keyword filter is exact match)
		if company_name and company_name not in payload.get("company_name", ""):
			continue

		results.append({
			"report_name": payload.get("report_name", ""),
			"chunk_index": payload.get("chunk_index", 0),
			"content": payload.get("content", ""),
			"company_name": payload.get("company_name", ""),
			"company_code": payload.get("company_code", ""),
			"year": payload.get("year", 0),
			"market": payload.get("market", ""),
			"score": r.get("score", 0.0),
			"classifications": payload.get("classifications", []),
		})

	return {
		"results": results,
		"count": len(results),
		"query": query,
		"search_type": "vector",
	}


def fulltext_search(query, limit=10, year=None, company_name=None, classification=None):
	"""
	Perform MariaDB full-text search on Report Chunks.

	Args:
		query: search query text
		limit: max results
		year: optional year filter
		company_name: optional company name filter
		classification: optional classification code filter

	Returns:
		dict with results list
	"""
	ft_query = _prepare_fulltext_query(query)
	conditions = []
	params = {"query": ft_query, "limit": limit}
	joins = ""

	# MariaDB full-text search using MATCH AGAINST
	match_clause = "MATCH(rc.content) AGAINST(%(query)s IN BOOLEAN MODE)"

	if year:
		conditions.append("cr.year = %(year)s")
		params["year"] = int(year)

	if company_name:
		conditions.append("cr.company_name LIKE %(company_name)s")
		params["company_name"] = f"%{company_name}%"

	if classification:
		joins = "JOIN `tabReport Classification` rcl ON rcl.parent = cr.name"
		conditions.append("rcl.category_code = %(classification)s")
		params["classification"] = classification

	where_clause = f"WHERE {match_clause}"
	if conditions:
		where_clause += " AND " + " AND ".join(conditions)

	sql = f"""
		SELECT
			rc.report as report_name,
			rc.chunk_index,
			rc.content,
			cr.company_name,
			cr.company_code,
			cr.year,
			cr.market,
			{match_clause} as relevance
		FROM `tabReport Chunk` rc
		JOIN `tabCommittee Report` cr ON cr.name = rc.report
		{joins}
		{where_clause}
		ORDER BY relevance DESC
		LIMIT %(limit)s
	"""

	try:
		rows = frappe.db.sql(sql, params, as_dict=True)
	except Exception:
		rows = []

	# Fallback to LIKE search if FULLTEXT returned no results
	if not rows:
		rows = _like_search(query, limit, year, company_name, classification)

	# Normalize scores to 0-1 range
	max_relevance = max((r.get("relevance", 0) for r in rows), default=1) or 1

	# Fetch classifications for each report
	report_names = list({r["report_name"] for r in rows})
	classifications_map = _get_classifications_for_reports(report_names)

	results = []
	for r in rows:
		results.append({
			"report_name": r["report_name"],
			"chunk_index": r["chunk_index"],
			"content": r["content"],
			"company_name": r.get("company_name", ""),
			"company_code": r.get("company_code", ""),
			"year": r.get("year", 0),
			"market": r.get("market", ""),
			"score": float(r.get("relevance", 0)) / max_relevance,
			"classifications": classifications_map.get(r["report_name"], []),
		})

	return {
		"results": results,
		"count": len(results),
		"query": query,
		"search_type": "fulltext",
	}


def _prepare_fulltext_query(query):
	"""Prepare query for MariaDB FULLTEXT BOOLEAN MODE.

	MariaDB's default InnoDB FULLTEXT parser does not properly tokenize CJK
	(Japanese/Chinese/Korean) text.  Appending a ``*`` wildcard to each term
	enables prefix matching which works around the tokenisation gap.
	"""
	terms = query.strip().split()
	prepared = []
	for term in terms:
		# Strip existing boolean operators for safety
		clean = term.lstrip("+-~<>")
		if not clean:
			continue
		if _CJK_RE.search(clean):
			prepared.append(f"+{clean}*")
		else:
			prepared.append(f"+{clean}*" if len(clean) < 4 else f"+{clean}")
	return " ".join(prepared) if prepared else query


def _like_search(query, limit, year=None, company_name=None, classification=None):
	"""Fallback LIKE-based search when FULLTEXT is not available."""
	conditions = ["rc.content LIKE %(query_like)s"]
	params = {"query_like": f"%{query}%", "limit": limit}
	joins = ""

	if year:
		conditions.append("cr.year = %(year)s")
		params["year"] = int(year)

	if company_name:
		conditions.append("cr.company_name LIKE %(company_name)s")
		params["company_name"] = f"%{company_name}%"

	if classification:
		joins = "JOIN `tabReport Classification` rcl ON rcl.parent = cr.name"
		conditions.append("rcl.category_code = %(classification)s")
		params["classification"] = classification

	where_clause = " AND ".join(conditions)

	sql = f"""
		SELECT
			rc.report as report_name,
			rc.chunk_index,
			rc.content,
			cr.company_name,
			cr.company_code,
			cr.year,
			cr.market,
			1.0 as relevance
		FROM `tabReport Chunk` rc
		JOIN `tabCommittee Report` cr ON cr.name = rc.report
		{joins}
		WHERE {where_clause}
		LIMIT %(limit)s
	"""

	return frappe.db.sql(sql, params, as_dict=True)


def _group_by_report(results):
	"""Group chunk-level results into report-level results."""
	report_map = {}
	for r in results:
		rn = r["report_name"]
		current_score = r.get("hybrid_score") or r.get("score", 0)
		if rn not in report_map:
			report_map[rn] = {
				**r,
				"matched_chunks": 1,
				"best_score": current_score,
			}
		else:
			report_map[rn]["matched_chunks"] += 1
			if current_score > report_map[rn]["best_score"]:
				# Keep the chunk-level fields from the best scoring chunk
				matched_chunks = report_map[rn]["matched_chunks"]
				report_map[rn] = {
					**r,
					"matched_chunks": matched_chunks,
					"best_score": current_score,
				}
	return sorted(report_map.values(), key=lambda x: x["best_score"], reverse=True)


def _get_classifications_for_reports(report_names):
	"""Fetch classification codes for a list of report names."""
	if not report_names:
		return {}

	placeholders = ", ".join(["%s"] * len(report_names))
	rows = frappe.db.sql(
		f"""
		SELECT parent, category_code
		FROM `tabReport Classification`
		WHERE parent IN ({placeholders})
		ORDER BY parent, layer, category_code
		""",
		tuple(report_names),
		as_dict=True,
	)

	result = {}
	for row in rows:
		result.setdefault(row["parent"], []).append(row["category_code"])
	return result


def find_similar(report_name, limit=5):
	"""
	Find reports similar to a given report.

	Args:
		report_name: Committee Report name
		limit: max results

	Returns:
		dict with similar reports
	"""
	# Get the first chunk of the report for comparison
	chunks = frappe.get_all(
		"Report Chunk",
		filters={"report": report_name},
		fields=["content"],
		order_by="chunk_index asc",
		limit_page_length=1,
	)

	if not chunks:
		return {"results": [], "count": 0}

	# Use the first chunk as the query
	query_text = chunks[0]["content"][:2000]
	results = vector_search(query_text, limit=limit + 5)

	# Filter out chunks from the same report
	filtered = [
		r for r in results.get("results", [])
		if r["report_name"] != report_name
	]

	# Deduplicate by report_name (keep highest scoring)
	seen = set()
	unique_results = []
	for r in filtered:
		if r["report_name"] not in seen:
			seen.add(r["report_name"])
			unique_results.append(r)
			if len(unique_results) >= limit:
				break

	return {
		"results": unique_results,
		"count": len(unique_results),
		"source_report": report_name,
		"search_type": "similar",
	}
