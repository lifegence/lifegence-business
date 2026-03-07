# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

"""
Tests for Lifegence Compliance

Covers: Committee Report CRUD, Report Chunk management,
classification taxonomy, search API validation, and PDF service.
"""

import frappe
from frappe.tests.utils import FrappeTestCase
from unittest.mock import patch, MagicMock


TEST_COMPANY_PREFIX = "__test_compliance__"

# Track test-created records for cleanup
_test_report_names = []


def _ensure_compliance_settings():
    """Ensure Compliance Settings singleton exists."""
    try:
        settings = frappe.get_single("Compliance Settings")
        if not settings.chunk_size:
            settings.db_set("chunk_size", 1000, update_modified=False)
            settings.db_set("chunk_overlap", 200, update_modified=False)
            settings.db_set("embedding_dimension", 768, update_modified=False)
            frappe.db.commit()
    except Exception:
        pass


def _ensure_classification_categories():
    """Ensure at least one classification category exists."""
    if frappe.db.count("Classification Category") == 0:
        cat = frappe.new_doc("Classification Category")
        cat.category_code = "A01"
        cat.category_name = "Test Category"
        cat.category_name_en = "Test Category EN"
        cat.layer = "A"
        cat.description = "Test classification category"
        cat.insert(ignore_permissions=True)
        frappe.db.commit()


def _create_test_report(**kwargs):
    """Create a test Committee Report with trackable company name."""
    defaults = {
        "filename": "test_report.pdf",
        "year": 2024,
        "company_name": f"{TEST_COMPANY_PREFIX} Company",
        "company_code": "1234",
        "market": "Prime",
        "indexing_status": "Pending",
        "classification_status": "Pending",
    }
    defaults.update(kwargs)
    # Ensure company_name is prefixed for cleanup
    if not defaults["company_name"].startswith(TEST_COMPANY_PREFIX):
        defaults["company_name"] = f"{TEST_COMPANY_PREFIX} {defaults['company_name']}"
    report = frappe.new_doc("Committee Report")
    for key, val in defaults.items():
        setattr(report, key, val)
    report.insert(ignore_permissions=True)
    frappe.db.commit()
    _test_report_names.append(report.name)
    return report


def _cleanup_test_data():
    """Remove only test-created reports and their chunks."""
    # Get test reports by company_name prefix
    test_reports = frappe.get_all(
        "Committee Report",
        filters={"company_name": ["like", f"{TEST_COMPANY_PREFIX}%"]},
        pluck="name"
    )
    # Delete linked chunks first
    for report_name in test_reports:
        chunks = frappe.get_all("Report Chunk", filters={"report": report_name}, pluck="name")
        for chunk_name in chunks:
            frappe.delete_doc("Report Chunk", chunk_name, force=True, ignore_permissions=True)
    # Then delete reports
    for report_name in test_reports:
        frappe.delete_doc("Committee Report", report_name, force=True, ignore_permissions=True)
    frappe.db.commit()
    _test_report_names.clear()


# ── Committee Report CRUD ─────────────────────────


class TestCommitteeReport(FrappeTestCase):
    """Test Committee Report document CRUD."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        _ensure_compliance_settings()

    def tearDown(self):
        _cleanup_test_data()

    def test_create_report(self):
        """Committee Report creates with required fields."""
        report = _create_test_report()
        self.assertIsNotNone(report.name)
        self.assertEqual(report.filename, "test_report.pdf")
        self.assertEqual(report.year, 2024)
        self.assertTrue(report.company_name.startswith(TEST_COMPANY_PREFIX))

    def test_report_requires_filename(self):
        """Report without filename raises error."""
        report = frappe.new_doc("Committee Report")
        report.year = 2024
        report.company_name = "No File"
        self.assertRaises(Exception, report.insert, ignore_permissions=True)

    def test_report_requires_year(self):
        """Report without year raises error."""
        report = frappe.new_doc("Committee Report")
        report.filename = "nofile.pdf"
        report.company_name = "No Year"
        self.assertRaises(Exception, report.insert, ignore_permissions=True)

    def test_report_default_statuses(self):
        """New report has Pending indexing and classification status."""
        report = _create_test_report()
        self.assertEqual(report.indexing_status, "Pending")
        self.assertEqual(report.classification_status, "Pending")

    def test_report_update_indexing_status(self):
        """Can update indexing_status on report."""
        report = _create_test_report()
        report.db_set("indexing_status", "Indexed")
        report.reload()
        self.assertEqual(report.indexing_status, "Indexed")


# ── Report Chunk ──────────────────────────────────


class TestReportChunk(FrappeTestCase):
    """Test Report Chunk creation and linking."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        _ensure_compliance_settings()

    def tearDown(self):
        _cleanup_test_data()

    def test_create_chunk(self):
        """Report Chunk creates linked to a report."""
        report = _create_test_report()
        chunk = frappe.new_doc("Report Chunk")
        chunk.report = report.name
        chunk.chunk_index = 0
        chunk.content = "This is test chunk content for compliance analysis."
        chunk.insert(ignore_permissions=True)
        frappe.db.commit()

        self.assertIsNotNone(chunk.name)
        self.assertEqual(chunk.report, report.name)
        self.assertEqual(chunk.chunk_index, 0)

    def test_multiple_chunks_for_report(self):
        """Multiple chunks can be created for a single report."""
        report = _create_test_report()
        for i in range(3):
            chunk = frappe.new_doc("Report Chunk")
            chunk.report = report.name
            chunk.chunk_index = i
            chunk.content = f"Chunk content {i}"
            chunk.insert(ignore_permissions=True)
        frappe.db.commit()

        count = frappe.db.count("Report Chunk", {"report": report.name})
        self.assertEqual(count, 3)

    def test_chunk_has_embedding_default(self):
        """Report Chunk has_embedding defaults to 0."""
        report = _create_test_report()
        chunk = frappe.new_doc("Report Chunk")
        chunk.report = report.name
        chunk.chunk_index = 0
        chunk.content = "Test content"
        chunk.insert(ignore_permissions=True)
        frappe.db.commit()

        self.assertEqual(chunk.has_embedding, 0)


# ── Classification Taxonomy ───────────────────────


class TestClassificationTaxonomy(FrappeTestCase):
    """Test classification categories and taxonomy API."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        _ensure_compliance_settings()
        _ensure_classification_categories()

    def test_classification_category_creation(self):
        """Classification Category creates with required fields."""
        cat = frappe.db.get_value(
            "Classification Category",
            {"category_code": "A01"},
            ["category_code", "layer", "category_name"],
            as_dict=True
        )
        self.assertIsNotNone(cat)
        self.assertEqual(cat.layer, "A")

    def test_taxonomy_api_returns_layers(self):
        """get_taxonomy returns layers A, B, C."""
        from lifegence_business.compliance.api.classification import get_taxonomy
        result = get_taxonomy()
        self.assertIn("layers", result)
        self.assertIn("A", result["layers"])
        self.assertIn("B", result["layers"])
        self.assertIn("C", result["layers"])

    def test_taxonomy_layer_names(self):
        """Taxonomy layers have correct Japanese names."""
        from lifegence_business.compliance.api.classification import get_taxonomy
        result = get_taxonomy()
        self.assertEqual(result["layers"]["A"]["name_en"], "Incident Types")


# ── Reports API ───────────────────────────────────


class TestReportsAPI(FrappeTestCase):
    """Test Reports API endpoints."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        _ensure_compliance_settings()

    def tearDown(self):
        _cleanup_test_data()

    def test_get_reports_pagination(self):
        """get_reports returns paginated results scoped to test data."""
        for i in range(3):
            _create_test_report(filename=f"report_{i}.pdf", company_name=f"Company {i}")

        from lifegence_business.compliance.api.reports import get_reports
        result = get_reports(page=1, limit=2, company_name=TEST_COMPANY_PREFIX)
        self.assertEqual(len(result["data"]), 2)
        self.assertEqual(result["pagination"]["total"], 3)
        self.assertEqual(result["pagination"]["total_pages"], 2)

    def test_get_reports_filter_by_year(self):
        """get_reports filters by year within test data."""
        _create_test_report(filename="r2023.pdf", year=2023, company_name="C2023")
        _create_test_report(filename="r2024.pdf", year=2024, company_name="C2024")

        from lifegence_business.compliance.api.reports import get_reports
        result = get_reports(year=2023, company_name=TEST_COMPANY_PREFIX)
        self.assertEqual(len(result["data"]), 1)
        self.assertEqual(result["data"][0]["year"], 2023)

    def test_get_report_detail(self):
        """get_report returns full report details."""
        report = _create_test_report()
        from lifegence_business.compliance.api.reports import get_report
        result = get_report(report.name)
        self.assertTrue(result["company_name"].startswith(TEST_COMPANY_PREFIX))
        self.assertEqual(result["year"], 2024)


# ── Classification API ────────────────────────────


class TestClassificationAPI(FrappeTestCase):
    """Test classification API endpoints."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        _ensure_compliance_settings()
        _ensure_classification_categories()

    def tearDown(self):
        _cleanup_test_data()

    def test_get_stats(self):
        """get_stats returns total and classified counts."""
        _create_test_report()
        from lifegence_business.compliance.api.classification import get_stats
        result = get_stats()
        self.assertIn("total_reports", result)
        self.assertIn("classified_reports", result)
        self.assertGreaterEqual(result["total_reports"], 1)

    def test_get_report_classification_empty(self):
        """get_report_classification returns empty for unclassified report."""
        report = _create_test_report()
        from lifegence_business.compliance.api.classification import get_report_classification
        result = get_report_classification(report.name)
        self.assertEqual(len(result["classifications"]), 0)
        self.assertEqual(result["classification_status"], "Pending")


# ── Search API Validation ─────────────────────────


class TestSearchAPIValidation(FrappeTestCase):
    """Test search API parameter validation."""

    def test_hybrid_search_requires_query(self):
        """hybrid_search without query raises error."""
        from lifegence_business.compliance.api.search import hybrid_search
        self.assertRaises(Exception, hybrid_search, query=None)

    def test_vector_search_requires_query(self):
        """vector_search without query raises error."""
        from lifegence_business.compliance.api.search import vector_search
        self.assertRaises(Exception, vector_search, query=None)

    def test_fulltext_search_requires_query(self):
        """fulltext_search without query raises error."""
        from lifegence_business.compliance.api.search import fulltext_search
        self.assertRaises(Exception, fulltext_search, query=None)

    def test_find_similar_requires_report_name(self):
        """find_similar without report_name raises error."""
        from lifegence_business.compliance.api.search import find_similar
        self.assertRaises(Exception, find_similar, report_name=None)
