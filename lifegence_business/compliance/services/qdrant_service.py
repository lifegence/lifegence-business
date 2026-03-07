# Copyright (c) 2025, Lifegence and contributors
# For license information, please see license.txt

import frappe


def get_settings():
	"""Get Compliance Settings singleton values."""
	return frappe.get_single("Compliance Settings")


def get_client():
	"""Create and return a Qdrant client from settings."""
	from qdrant_client import QdrantClient

	settings = get_settings()
	host = settings.qdrant_host or "localhost"
	port = int(settings.qdrant_port or 6333)
	api_key = settings.get_password("qdrant_api_key") if settings.qdrant_api_key else None
	use_https = bool(settings.qdrant_use_https)

	return QdrantClient(
		host=host,
		port=port,
		api_key=api_key,
		https=use_https,
	)


def get_collection_name():
	"""Get the collection name from settings."""
	settings = get_settings()
	return settings.qdrant_collection_name or "committee_reports"


def ensure_collection():
	"""Ensure the Qdrant collection exists with correct configuration."""
	from qdrant_client.models import (
		Distance, HnswConfigDiff, PayloadSchemaType, VectorParams,
	)

	client = get_client()
	collection_name = get_collection_name()
	settings = get_settings()
	dimension = int(settings.embedding_dimension or 768)

	collections = client.get_collections().collections
	existing_names = [c.name for c in collections]

	if collection_name not in existing_names:
		client.create_collection(
			collection_name=collection_name,
			vectors_config=VectorParams(
				size=dimension,
				distance=Distance.COSINE,
				hnsw_config=HnswConfigDiff(m=16, ef_construct=100),
			),
		)

		# Create payload indexes
		for field, schema in [
			("year", PayloadSchemaType.INTEGER),
			("company_code", PayloadSchemaType.KEYWORD),
			("report_name", PayloadSchemaType.KEYWORD),
			("classifications", PayloadSchemaType.KEYWORD),
		]:
			client.create_payload_index(
				collection_name=collection_name,
				field_name=field,
				field_schema=schema,
			)

		frappe.logger().info(f"Created Qdrant collection: {collection_name}")

	return collection_name


def upsert_vectors(points):
	"""
	Upsert vectors into Qdrant.

	Args:
		points: list of dicts with keys: id, vector, payload
	"""
	from qdrant_client.models import PointStruct

	client = get_client()
	collection_name = get_collection_name()

	qdrant_points = [
		PointStruct(
			id=p["id"],
			vector=p["vector"],
			payload=p["payload"],
		)
		for p in points
	]

	# Batch in groups of 100
	batch_size = 100
	for i in range(0, len(qdrant_points), batch_size):
		batch = qdrant_points[i : i + batch_size]
		client.upsert(collection_name=collection_name, points=batch)


def search_vectors(query_vector, limit=10, filters=None):
	"""
	Search for similar vectors in Qdrant.

	Args:
		query_vector: list of floats (embedding)
		limit: number of results
		filters: optional dict with filter conditions
			e.g. {"year": 2023, "company_code": "7841"}

	Returns:
		list of search results with score and payload
	"""
	from qdrant_client.models import FieldCondition, Filter, MatchValue

	client = get_client()
	collection_name = get_collection_name()

	qdrant_filter = None
	if filters:
		conditions = []
		for key, value in filters.items():
			conditions.append(
				FieldCondition(key=key, match=MatchValue(value=value))
			)
		qdrant_filter = Filter(must=conditions)

	results = client.query_points(
		collection_name=collection_name,
		query=query_vector,
		limit=limit,
		query_filter=qdrant_filter,
		with_payload=True,
	)

	return [
		{
			"id": str(point.id),
			"score": point.score,
			"payload": point.payload,
		}
		for point in results.points
	]


def delete_report_vectors(report_name):
	"""Delete all vectors associated with a report."""
	from qdrant_client.models import FieldCondition, Filter, MatchValue

	client = get_client()
	collection_name = get_collection_name()

	client.delete(
		collection_name=collection_name,
		points_selector=Filter(
			must=[
				FieldCondition(
					key="report_name",
					match=MatchValue(value=report_name),
				)
			]
		),
	)


def get_collection_info():
	"""Get information about the Qdrant collection."""
	client = get_client()
	collection_name = get_collection_name()

	try:
		info = client.get_collection(collection_name=collection_name)
		status = info.status
		if hasattr(status, "value"):
			status = status.value
		return {
			"name": collection_name,
			"points_count": info.points_count or 0,
			"indexed_vectors_count": info.indexed_vectors_count or 0,
			"status": str(status) if status else "unknown",
		}
	except Exception as e:
		frappe.logger().warning(f"Qdrant get_collection_info failed: {e}")
		return {"name": collection_name, "points_count": 0, "indexed_vectors_count": 0, "status": "not_found"}


def on_report_delete(doc, method):
	"""Hook called when a Committee Report is deleted."""
	try:
		delete_report_vectors(doc.name)
	except Exception as e:
		frappe.logger().warning(f"Failed to delete Qdrant vectors for {doc.name}: {e}")
