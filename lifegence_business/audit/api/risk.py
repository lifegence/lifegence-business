# Copyright (c) 2026, Lifegence and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import today


@frappe.whitelist()
def get_risk_matrix(department=None, risk_category=None, jsox_only=False):
	"""Get risk matrix (heatmap) data."""
	try:
		from lifegence_business.audit.services.risk_service import get_risk_matrix_data

		if isinstance(jsox_only, str):
			jsox_only = jsox_only.lower() in ("true", "1")

		data = get_risk_matrix_data(department, risk_category, jsox_only)
		return {"success": True, "data": data}
	except Exception as e:
		frappe.log_error(f"get_risk_matrix error: {e}")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_risk_summary(department=None, status=None):
	"""Get risk register summary."""
	try:
		from lifegence_business.audit.services.risk_service import get_risk_summary_data

		data = get_risk_summary_data(department, status)
		return {"success": True, "data": data}
	except Exception as e:
		frappe.log_error(f"get_risk_summary error: {e}")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def create_risk_assessment(risk_register, likelihood_score, impact_score, overall_assessment=None, mitigation_plan=None):
	"""Create a new risk assessment and update the risk register."""
	try:
		doc = frappe.get_doc({
			"doctype": "Risk Assessment",
			"risk_register": risk_register,
			"likelihood_score": str(likelihood_score),
			"impact_score": str(impact_score),
			"assessment_date": today(),
			"assessor": frappe.session.user,
			"overall_assessment": overall_assessment or "",
			"mitigation_plan": mitigation_plan or "",
		})
		doc.insert(ignore_permissions=True)

		return {
			"success": True,
			"data": {
				"assessment": doc.name,
				"risk_score": doc.risk_score,
				"risk_level": doc.risk_level,
				"score_trend": doc.score_trend,
			},
		}
	except Exception as e:
		frappe.log_error(f"create_risk_assessment error: {e}")
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_risk_trend(risk_register, period=None):
	"""Get risk score trend data for a specific risk."""
	try:
		filters = {"risk_register": risk_register}

		assessments = frappe.get_all(
			"Risk Assessment",
			filters=filters,
			fields=["name", "assessment_date", "risk_score", "risk_level", "likelihood_score", "impact_score", "score_trend"],
			order_by="assessment_date asc",
		)

		return {
			"success": True,
			"data": {
				"risk_register": risk_register,
				"assessments": assessments,
				"total_assessments": len(assessments),
			},
		}
	except Exception as e:
		frappe.log_error(f"get_risk_trend error: {e}")
		return {"success": False, "error": str(e)}
