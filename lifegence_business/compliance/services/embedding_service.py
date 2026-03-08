# Copyright (c) 2025, Lifegence and contributors
# For license information, please see license.txt

import time

import frappe


def _configure_genai():
	"""Configure the Gemini API client."""
	import google.generativeai as genai

	from lifegence_business.compliance.doctype.compliance_settings.compliance_settings import ComplianceSettings
	settings = frappe.get_single("Compliance Settings")
	api_key = ComplianceSettings.get_gemini_api_key()
	if not api_key:
		frappe.throw("Gemini API Key is not configured in Compliance Settings or Company OS AI Settings")
	genai.configure(api_key=api_key)
	return settings, genai


def _embed_kwargs(settings):
	"""Build extra kwargs for genai.embed_content (e.g. output_dimensionality)."""
	dimension = int(settings.embedding_dimension or 768)
	model = settings.embedding_model or "gemini-embedding-001"
	# gemini-embedding-001 outputs 3072 dims by default; truncate to configured dim
	if "gemini-embedding" in model and dimension < 3072:
		return {"output_dimensionality": dimension}
	return {}


def generate_embedding(text):
	"""
	Generate an embedding vector for a single text.

	Args:
		text: input text string

	Returns:
		list of floats (embedding vector)
	"""
	settings, genai = _configure_genai()
	model = settings.embedding_model or "gemini-embedding-001"

	result = genai.embed_content(
		model=f"models/{model}",
		content=text,
		task_type="retrieval_document",
		**_embed_kwargs(settings),
	)

	return result["embedding"]


def generate_query_embedding(text):
	"""
	Generate an embedding vector for a search query.

	Args:
		text: query text string

	Returns:
		list of floats (embedding vector)
	"""
	settings, genai = _configure_genai()
	model = settings.embedding_model or "gemini-embedding-001"

	result = genai.embed_content(
		model=f"models/{model}",
		content=text,
		task_type="retrieval_query",
		**_embed_kwargs(settings),
	)

	return result["embedding"]


def generate_batch(texts, task_type="retrieval_document", delay=0.1):
	"""
	Generate embeddings for a batch of texts with rate limiting.

	Args:
		texts: list of text strings
		task_type: "retrieval_document" or "retrieval_query"
		delay: seconds between API calls (rate limiting)

	Returns:
		list of embedding vectors (list of list of floats)
	"""
	settings, genai = _configure_genai()
	model = settings.embedding_model or "gemini-embedding-001"
	extra_kwargs = _embed_kwargs(settings)
	embeddings = []

	for text in texts:
		try:
			result = genai.embed_content(
				model=f"models/{model}",
				content=text,
				task_type=task_type,
				**extra_kwargs,
			)
			embeddings.append(result["embedding"])
		except Exception as e:
			frappe.logger().warning(f"Embedding generation failed: {e}")
			# Return zero vector as fallback
			dimension = int(settings.embedding_dimension or 768)
			embeddings.append([0.0] * dimension)

		if delay > 0:
			time.sleep(delay)

	return embeddings


def chunk_text(text, chunk_size=None, chunk_overlap=None, min_chunk_size=100):
	"""
	Split text into overlapping chunks.

	Args:
		text: input text
		chunk_size: max chars per chunk (from settings if None)
		chunk_overlap: overlap chars between chunks (from settings if None)
		min_chunk_size: minimum chunk size to keep

	Returns:
		list of dicts with keys: index, content, offset, length
	"""
	if not text or not text.strip():
		return []

	settings = frappe.get_single("Compliance Settings")
	if chunk_size is None:
		chunk_size = int(settings.chunk_size or 1000)
	if chunk_overlap is None:
		chunk_overlap = int(settings.chunk_overlap or 200)

	chunks = []
	start = 0
	index = 0

	while start < len(text):
		end = start + chunk_size

		# Try to break at sentence boundary
		if end < len(text):
			# Look for sentence endings near the chunk boundary
			search_start = max(end - 100, start)
			search_text = text[search_start:end]

			# Japanese sentence endings
			for sep in ["。", "．", "\n\n", "\n", ".", "!", "?", "！", "？"]:
				last_pos = search_text.rfind(sep)
				if last_pos != -1 and last_pos > len(search_text) // 2:
					end = search_start + last_pos + len(sep)
					break

		chunk_text_content = text[start:end].strip()

		if len(chunk_text_content) >= min_chunk_size:
			chunks.append({
				"index": index,
				"content": chunk_text_content,
				"offset": start,
				"length": len(chunk_text_content),
			})
			index += 1

		start = end - chunk_overlap
		if start <= chunks[-1]["offset"] if chunks else 0:
			start = end

	return chunks
