# Copyright (c) 2025, Lifegence and contributors
# For license information, please see license.txt

import json

import frappe
from typing import Dict, Any, Optional


@frappe.whitelist()
def list_pending_contracts(
	limit: int = 20,
	priority: Optional[str] = None,
) -> Dict[str, Any]:
	"""List contracts awaiting approval."""
	try:
		filters = {"status": "Pending Approval"}
		if priority:
			filters["priority"] = priority

		contracts = frappe.get_all(
			"Contract",
			filters=filters,
			fields=[
				"name", "title", "contract_type", "priority",
				"party_name", "counterparty_name", "contract_amount",
				"currency", "start_date", "end_date", "current_approver",
			],
			order_by="creation desc",
			limit_page_length=limit,
		)

		return {
			"success": True,
			"count": len(contracts),
			"contracts": contracts,
		}

	except Exception as e:
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def submit_contract_for_approval(contract_name: str) -> Dict[str, Any]:
	"""Submit a contract for approval."""
	try:
		if not frappe.db.exists("Contract", contract_name):
			return {"success": False, "error": f"Contract '{contract_name}' does not exist"}

		if not frappe.has_permission("Contract", "write", contract_name):
			return {"success": False, "error": f"No write permission for Contract '{contract_name}'"}

		contract = frappe.get_doc("Contract", contract_name)

		if contract.status != "Draft":
			return {
				"success": False,
				"error": f"Contract is not in Draft status (current: {contract.status})"
			}

		contract.status = "Pending Approval"
		contract.save()

		return {
			"success": True,
			"contract_name": contract_name,
			"message": f"Contract '{contract.title}' submitted for approval",
		}

	except Exception as e:
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def request_esignature(
	contract_name: str,
	signers: str | list,
	provider_name: Optional[str] = None,
) -> Dict[str, Any]:
	"""Create an e-signature request for an approved contract.

	Args:
		signers: JSON string or list of signers, each with 'name' and 'email'.
	"""
	try:
		if not frappe.db.exists("Contract", contract_name):
			return {"success": False, "error": f"Contract '{contract_name}' does not exist"}

		contract_status = frappe.db.get_value("Contract", contract_name, "status")
		if contract_status not in ("Approved", "Active"):
			return {
				"success": False,
				"error": f"Contract must be Approved or Active (current: {contract_status})"
			}

		from lifegence_business.contract_approval.api.esignature import create_signature_request

		# Ensure signers is a JSON string for the API
		if isinstance(signers, list):
			signers = json.dumps(signers, ensure_ascii=False)

		result = create_signature_request(
			contract_name=contract_name,
			signers=signers,
			provider_name=provider_name,
		)
		return result

	except Exception as e:
		return {"success": False, "error": str(e)}
