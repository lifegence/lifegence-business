# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from typing import Dict, Any, Optional


@frappe.whitelist()
def get_audit_status_summary(fiscal_year: Optional[str] = None) -> Dict[str, Any]:
	"""Get audit status summary for AI chat."""
	try:
		from lifegence_audit.api.audit import get_audit_dashboard

		result = get_audit_dashboard(fiscal_year=fiscal_year)
		if not result.get("success"):
			return {"success": False, "error": result.get("error", "不明なエラー")}

		data = result["data"]
		return {
			"success": True,
			"fiscal_year": fiscal_year or "全期間",
			"plan_summary": data.get("plan_summary", {}),
			"findings_summary": data.get("findings_summary", {}),
			"corrective_actions_summary": data.get("corrective_actions_summary", {}),
			"risk_summary": data.get("risk_summary", {}),
		}

	except Exception as e:
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_risk_assessment_guide(
	risk_description: str,
	department: Optional[str] = None,
) -> Dict[str, Any]:
	"""Provide risk assessment guidance."""
	try:
		guide = {
			"success": True,
			"risk_description": risk_description,
			"likelihood_criteria": {
				"1": "極めて低い: 10年に1回以下",
				"2": "低い: 5-10年に1回程度",
				"3": "中程度: 1-5年に1回程度",
				"4": "高い: 年に1回程度",
				"5": "極めて高い: 月に1回以上",
			},
			"impact_criteria": {
				"1": "軽微: 業務への影響なし",
				"2": "小: 一時的な業務遅延",
				"3": "中: 部門業務に影響",
				"4": "大: 全社的な業務影響",
				"5": "甚大: 事業継続に関わる重大な影響",
			},
			"risk_levels": {
				"Critical": "20-25: 即時対応が必要",
				"High": "12-19: 早期の対応が必要",
				"Medium": "6-11: 計画的な対応が必要",
				"Low": "1-5: モニタリング継続",
			},
		}
		if department:
			guide["department"] = department

		return guide

	except Exception as e:
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def analyze_findings(
	period: Optional[str] = None,
	department: Optional[str] = None,
	category: Optional[str] = None,
) -> Dict[str, Any]:
	"""Analyze audit finding trends."""
	try:
		filters = {}
		if category:
			filters["category"] = category

		findings = frappe.get_all(
			"Audit Finding",
			filters=filters,
			fields=["severity", "category", "status", "finding_date", "audit_engagement"],
		)

		if not findings:
			return {"success": True, "count": 0, "message": "分析対象の発見事項がありません。"}

		by_category = {}
		by_severity = {}
		by_status = {}
		for f in findings:
			by_category[f.category] = by_category.get(f.category, 0) + 1
			by_severity[f.severity] = by_severity.get(f.severity, 0) + 1
			by_status[f.status] = by_status.get(f.status, 0) + 1

		return {
			"success": True,
			"count": len(findings),
			"by_category": by_category,
			"by_severity": by_severity,
			"by_status": by_status,
		}

	except Exception as e:
		return {"success": False, "error": str(e)}
