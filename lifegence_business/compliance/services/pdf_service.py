# Copyright (c) 2025, Lifegence and contributors
# For license information, please see license.txt

import hashlib
import os

import fitz  # PyMuPDF


def extract_text(file_path):
	"""
	Extract full text from a PDF file.

	Args:
		file_path: absolute path to the PDF file

	Returns:
		dict with keys: text, page_count
	"""
	if not os.path.isfile(file_path):
		raise FileNotFoundError(f"PDF file not found: {file_path}")

	doc = fitz.open(file_path)
	page_count = doc.page_count
	pages_text = []

	for page in doc:
		text = page.get_text("text")
		if text.strip():
			pages_text.append(text)

	doc.close()

	return {
		"text": "\n".join(pages_text),
		"page_count": page_count,
	}


def extract_by_pages(file_path):
	"""
	Extract text page by page from a PDF.

	Args:
		file_path: absolute path to the PDF file

	Returns:
		list of dicts with keys: page_number, text
	"""
	if not os.path.isfile(file_path):
		raise FileNotFoundError(f"PDF file not found: {file_path}")

	doc = fitz.open(file_path)
	pages = []

	for i, page in enumerate(doc):
		text = page.get_text("text")
		pages.append({
			"page_number": i + 1,
			"text": text,
		})

	doc.close()
	return pages


def compute_file_hash(file_path):
	"""
	Compute SHA-256 hash of a file.

	Args:
		file_path: absolute path to the file

	Returns:
		hex string of the SHA-256 hash
	"""
	if not os.path.isfile(file_path):
		raise FileNotFoundError(f"File not found: {file_path}")

	sha256 = hashlib.sha256()
	with open(file_path, "rb") as f:
		for chunk in iter(lambda: f.read(8192), b""):
			sha256.update(chunk)

	return sha256.hexdigest()


def get_page_count(file_path):
	"""Get page count without extracting text."""
	if not os.path.isfile(file_path):
		raise FileNotFoundError(f"PDF file not found: {file_path}")

	doc = fitz.open(file_path)
	count = doc.page_count
	doc.close()
	return count
