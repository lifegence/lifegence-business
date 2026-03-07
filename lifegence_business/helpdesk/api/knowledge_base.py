# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe import _


@frappe.whitelist()
def search_knowledge_base(query=None, category=None, visibility=None):
	"""Search knowledge base articles by keyword, category, and visibility."""
	filters = {"status": "Published"}

	if category:
		filters["category"] = category

	if visibility:
		if visibility == "外部公開":
			filters["visibility"] = ["in", ["外部公開", "両方"]]
		elif visibility == "内部のみ":
			filters["visibility"] = ["in", ["内部のみ", "両方"]]
		else:
			filters["visibility"] = visibility

	or_filters = {}
	if query:
		or_filters = {
			"title": ["like", f"%{query}%"],
			"content": ["like", f"%{query}%"],
			"tags": ["like", f"%{query}%"],
		}

	articles = frappe.get_all(
		"HD Knowledge Base",
		filters=filters,
		or_filters=or_filters if or_filters else None,
		fields=[
			"name", "title", "category", "visibility",
			"tags", "helpful_count", "view_count", "author",
			"creation",
		],
		order_by="helpful_count desc, creation desc",
		limit=20,
	)

	return {"success": True, "articles": articles, "count": len(articles)}


@frappe.whitelist()
def mark_helpful(article):
	"""Increment the helpful count for a knowledge base article."""
	if not frappe.db.exists("HD Knowledge Base", article):
		return {"success": False, "error": _("記事 {0} は存在しません。").format(article)}

	doc = frappe.get_doc("HD Knowledge Base", article)
	doc.helpful_count = (doc.helpful_count or 0) + 1
	doc.save(ignore_permissions=True)

	return {
		"success": True,
		"article": doc.name,
		"helpful_count": doc.helpful_count,
	}
