# Copyright (c) 2025, Lifegence and contributors
# For license information, please see license.txt

import json
import os
import re

import frappe
from bs4 import BeautifulSoup

from lifegence_business.compliance.services.pdf_service import compute_file_hash


def parse_year_page(year_dir):
	"""
	Parse a year directory to extract report metadata from index.html and links.json.

	Expected structure:
		year_dir/
		├── index.html      # Metadata table from daisanshaiinkai.com
		├── links.json       # URLs and filenames
		└── files/
		    ├── report1.pdf
		    └── report2.pdf

	Args:
		year_dir: path to the year directory (e.g., .../downloaded_reports/2023/)

	Returns:
		list of dicts with report metadata
	"""
	reports = []
	year = os.path.basename(year_dir)

	if not year.isdigit():
		return reports

	# Load links.json for URL mapping
	links_path = os.path.join(year_dir, "links.json")
	url_map = {}
	if os.path.isfile(links_path):
		with open(links_path, "r", encoding="utf-8") as f:
			links_data = json.load(f)
			for entry in links_data:
				filename = entry.get("filename", "")
				url = entry.get("url", "")
				if filename:
					url_map[filename] = url

	# Parse index.html for metadata
	html_metadata = _parse_index_html(os.path.join(year_dir, "index.html"))

	# Scan files directory
	files_dir = os.path.join(year_dir, "files")
	if not os.path.isdir(files_dir):
		return reports

	for filename in sorted(os.listdir(files_dir)):
		if not filename.lower().endswith(".pdf"):
			continue

		file_path = os.path.join(files_dir, filename)
		source_url = url_map.get(filename, "")

		# Try to match metadata from HTML
		meta = _match_metadata(filename, source_url, html_metadata)

		reports.append({
			"filename": filename,
			"file_path": file_path,
			"source_url": source_url,
			"year": int(year),
			"company_name": meta.get("company_name", _extract_company_from_filename(filename)),
			"company_code": meta.get("company_code", ""),
			"market": meta.get("market", ""),
			"auditor": meta.get("auditor", ""),
			"committee_members": meta.get("committee_members", ""),
			"purpose": meta.get("purpose", ""),
		})

	return reports


def _parse_index_html(html_path):
	"""
	Parse the index.html from daisanshaiinkai.com to extract metadata.

	Returns:
		list of dicts with metadata keyed by URL or company name
	"""
	if not os.path.isfile(html_path):
		return []

	with open(html_path, "r", encoding="utf-8") as f:
		soup = BeautifulSoup(f.read(), "lxml")

	entries = []
	tables = soup.find_all("table")

	for table in tables:
		rows = table.find_all("tr")
		headers = []

		for row in rows:
			cells = row.find_all(["th", "td"])
			cell_texts = [c.get_text(strip=True) for c in cells]

			if row.find("th"):
				headers = cell_texts
				continue

			if not headers or len(cell_texts) < 2:
				continue

			entry = {}
			for i, header in enumerate(headers):
				if i < len(cell_texts):
					value = cell_texts[i]
					header_lower = header.lower()

					if "会社" in header or "社名" in header or "企業" in header:
						entry["company_name"] = value
					elif "コード" in header or "証券" in header:
						entry["company_code"] = value
					elif "市場" in header:
						entry["market"] = value
					elif "監査" in header or "法人" in header:
						entry["auditor"] = value
					elif "委員" in header:
						entry["committee_members"] = value
					elif "目的" in header or "事由" in header:
						entry["purpose"] = value

			# Extract URL from links in the row
			links = row.find_all("a", href=True)
			for link in links:
				href = link["href"]
				if href.endswith(".pdf"):
					entry["url"] = href
				if not entry.get("company_name"):
					entry["company_name"] = link.get_text(strip=True)

			if entry.get("company_name") or entry.get("url"):
				entries.append(entry)

	return entries


def _match_metadata(filename, source_url, html_entries):
	"""Match a PDF file to its metadata from the HTML table."""
	if not html_entries:
		return {}

	# Try exact URL match
	for entry in html_entries:
		entry_url = entry.get("url", "")
		if entry_url and source_url:
			if _normalize_url(entry_url) == _normalize_url(source_url):
				return entry

	# Try filename match in URL
	for entry in html_entries:
		entry_url = entry.get("url", "")
		if entry_url and filename in entry_url:
			return entry

	return {}


def _normalize_url(url):
	"""Normalize a URL for comparison."""
	url = url.strip().rstrip("/")
	url = re.sub(r'^https?://', '', url)
	return url.lower()


def _extract_company_from_filename(filename):
	"""Try to extract company name from the PDF filename."""
	name = os.path.splitext(filename)[0]
	# Remove common prefixes/suffixes
	name = re.sub(r'^\d+[-_]?', '', name)
	name = re.sub(r'[-_]?\d+$', '', name)
	name = name.replace('_', ' ').replace('-', ' ').strip()
	return name or filename


def import_from_downloaded(base_path=None):
	"""
	Import all reports from the downloaded_reports directory.

	Args:
		base_path: base directory path. If None, reads from Compliance Settings.

	Returns:
		dict with keys: registered, skipped, errors
	"""
	if not base_path:
		settings = frappe.get_single("Compliance Settings")
		base_path = settings.reports_base_path

	if not os.path.isdir(base_path):
		frappe.throw(f"Reports base path not found: {base_path}")

	result = {"registered": 0, "skipped": 0, "errors": []}

	# Process each year directory
	for year_name in sorted(os.listdir(base_path)):
		year_dir = os.path.join(base_path, year_name)
		if not os.path.isdir(year_dir) or not year_name.isdigit():
			continue

		reports = parse_year_page(year_dir)

		for report_meta in reports:
			try:
				file_path = report_meta["file_path"]
				file_hash = compute_file_hash(file_path)

				# Check for duplicate
				if frappe.db.exists("Committee Report", {"file_hash": file_hash}):
					result["skipped"] += 1
					continue

				doc = frappe.get_doc({
					"doctype": "Committee Report",
					"filename": report_meta["filename"],
					"source_url": report_meta["source_url"],
					"file_hash": file_hash,
					"year": report_meta["year"],
					"company_name": report_meta["company_name"],
					"company_code": report_meta.get("company_code", ""),
					"market": report_meta.get("market", ""),
					"auditor": report_meta.get("auditor", ""),
					"committee_members": report_meta.get("committee_members", ""),
					"purpose": report_meta.get("purpose", ""),
					"indexing_status": "Pending",
					"classification_status": "Pending",
				})
				doc.insert(ignore_permissions=True)
				result["registered"] += 1

			except Exception as e:
				result["errors"].append({
					"filename": report_meta.get("filename", "unknown"),
					"error": str(e),
				})

		frappe.db.commit()

	return result


def import_all_years(base_path=None):
	"""Alias for import_from_downloaded."""
	return import_from_downloaded(base_path)
