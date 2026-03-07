import frappe
from frappe.utils import now_datetime


@frappe.whitelist()
def submit_for_approval(contract_name):
    """Submit a contract for approval."""
    contract = frappe.get_doc("Contract", contract_name)

    if contract.status != "Draft":
        frappe.throw("Only draft contracts can be submitted for approval")

    # Find matching approval rule
    rules = frappe.get_all(
        "Contract Approval Rule",
        filters={"is_active": 1},
        fields=["name", "contract_type", "min_amount", "max_amount", "approver_role", "approver_user"],
        order_by="min_amount desc",
    )

    approver = None
    for rule in rules:
        if rule.contract_type and rule.contract_type != contract.contract_type:
            continue
        if rule.min_amount and (contract.contract_amount or 0) < rule.min_amount:
            continue
        if rule.max_amount and (contract.contract_amount or 0) > rule.max_amount:
            continue

        approver = rule.approver_user
        if not approver and rule.approver_role:
            users = frappe.get_all(
                "Has Role",
                filters={"role": rule.approver_role, "parenttype": "User"},
                fields=["parent"],
                limit=1,
            )
            if users:
                approver = users[0].parent
        break

    contract.db_set("status", "Pending Approval")
    if approver:
        contract.db_set("current_approver", approver)

    frappe.get_doc({
        "doctype": "Contract Approval Log",
        "contract": contract_name,
        "action": "Submitted for Approval",
        "action_by": frappe.session.user,
        "action_date": now_datetime(),
    }).insert(ignore_permissions=True)

    return {"success": True, "approver": approver}


@frappe.whitelist()
def approve_contract(contract_name, comments=None):
    """Approve a contract."""
    contract = frappe.get_doc("Contract", contract_name)

    if contract.status != "Pending Approval":
        frappe.throw("Contract is not pending approval")

    contract.db_set("status", "Approved")
    contract.db_set("approved_by", frappe.session.user)
    contract.db_set("approved_date", frappe.utils.today())
    contract.db_set("current_approver", None)

    frappe.get_doc({
        "doctype": "Contract Approval Log",
        "contract": contract_name,
        "action": "Approved",
        "action_by": frappe.session.user,
        "action_date": now_datetime(),
        "comments": comments,
    }).insert(ignore_permissions=True)

    return {"success": True}


@frappe.whitelist()
def reject_contract(contract_name, comments=None):
    """Reject a contract."""
    contract = frappe.get_doc("Contract", contract_name)

    if contract.status != "Pending Approval":
        frappe.throw("Contract is not pending approval")

    contract.db_set("status", "Rejected")
    contract.db_set("current_approver", None)

    frappe.get_doc({
        "doctype": "Contract Approval Log",
        "contract": contract_name,
        "action": "Rejected",
        "action_by": frappe.session.user,
        "action_date": now_datetime(),
        "comments": comments,
    }).insert(ignore_permissions=True)

    return {"success": True}
