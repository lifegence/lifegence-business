# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestHDKnowledgeBase(FrappeTestCase):
	"""Test cases for HD Knowledge Base DocType and search API."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls._ensure_roles()
		cls._ensure_category()

	@classmethod
	def _ensure_roles(cls):
		for role_name in ("Support Manager", "Support Agent"):
			if not frappe.db.exists("Role", role_name):
				frappe.get_doc({
					"doctype": "Role",
					"role_name": role_name,
					"desk_access": 1,
				}).insert(ignore_permissions=True)

	@classmethod
	def _ensure_category(cls):
		if not frappe.db.exists("HD Category", "IT"):
			frappe.get_doc({
				"doctype": "HD Category",
				"category_name": "IT",
				"description": "IT関連",
				"enabled": 1,
			}).insert(ignore_permissions=True)
			frappe.db.commit()

	def _create_article(self, **kwargs):
		defaults = {
			"doctype": "HD Knowledge Base",
			"title": "テスト記事",
			"content": "テスト記事の内容です。",
			"status": "Published",
			"visibility": "内部のみ",
			"category": "IT",
		}
		defaults.update(kwargs)
		doc = frappe.get_doc(defaults)
		doc.insert(ignore_permissions=True)
		return doc

	# ─── TC-KB01: Create Article ────────────────────────────────────

	def test_create_article(self):
		"""TC-KB01: Create knowledge base article with naming series KB-."""
		article = self._create_article()
		self.assertTrue(article.name.startswith("KB-"))
		self.assertEqual(article.status, "Published")
		self.assertEqual(article.author, frappe.session.user)

	# ─── TC-KB02: Search by Keyword ─────────────────────────────────

	def test_search_by_keyword(self):
		"""TC-KB02: Search articles by keyword."""
		self._create_article(
			title="VPN接続の方法",
			content="VPNに接続するには以下の手順に従ってください。",
			tags="VPN,ネットワーク",
		)

		from lifegence_business.helpdesk.api.knowledge_base import search_knowledge_base
		result = search_knowledge_base(query="VPN")

		self.assertTrue(result["success"])
		self.assertGreater(result["count"], 0)
		titles = [a["title"] for a in result["articles"]]
		self.assertIn("VPN接続の方法", titles)

	# ─── TC-KB03: Visibility Filter ─────────────────────────────────

	def test_visibility_filter(self):
		"""TC-KB03: Filter articles by visibility."""
		self._create_article(
			title="内部限定記事",
			content="社内限定の内容",
			visibility="内部のみ",
		)
		self._create_article(
			title="外部公開記事",
			content="一般公開の内容",
			visibility="外部公開",
		)

		from lifegence_business.helpdesk.api.knowledge_base import search_knowledge_base

		# Search for external-visible articles
		result = search_knowledge_base(visibility="外部公開")
		self.assertTrue(result["success"])
		visibilities = [a["visibility"] for a in result["articles"]]
		for v in visibilities:
			self.assertIn(v, ("外部公開", "両方"))

	# ─── TC-KB04: Helpful Count ─────────────────────────────────────

	def test_helpful_count(self):
		"""TC-KB04: Increment helpful count."""
		article = self._create_article(title="便利な記事")
		self.assertEqual(article.helpful_count, 0)

		from lifegence_business.helpdesk.api.knowledge_base import mark_helpful
		result = mark_helpful(article=article.name)

		self.assertTrue(result["success"])
		self.assertEqual(result["helpful_count"], 1)

		# Increment again
		result2 = mark_helpful(article=article.name)
		self.assertEqual(result2["helpful_count"], 2)
