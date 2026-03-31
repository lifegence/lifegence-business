import json

import frappe
from frappe.utils import add_days, now_datetime, today

# Allowlist of valid webhook event types
ALLOWED_EVENT_TYPES = {"Sent", "Viewed", "Signed", "Declined", "Expired", "Cancelled", "Error"}


@frappe.whitelist()
def create_signature_request(contract_name, signers, provider_name=None, expiry_days=None):
    """Create an e-signature request for an approved contract.

    Args:
        contract_name: Contract document name
        signers: JSON string of signers [{name, email, order}]
        provider_name: E-Signature Provider Settings name (optional, uses first enabled)
        expiry_days: Override default expiry days (optional)
    """
    contract = frappe.get_doc("Contract", contract_name)

    if contract.status not in ("Approved", "Active"):
        frappe.throw("E-Signature requests can only be created for Approved or Active contracts")

    # Resolve provider
    if not provider_name:
        providers = frappe.get_all(
            "E-Signature Provider Settings",
            filters={"enabled": 1},
            pluck="name",
            limit=1,
        )
        if not providers:
            frappe.throw("No enabled e-signature provider found")
        provider_name = providers[0]

    provider = frappe.get_doc("E-Signature Provider Settings", provider_name)

    # Parse and validate signers
    if isinstance(signers, str):
        try:
            signers_list = json.loads(signers)
        except json.JSONDecodeError:
            frappe.throw("Invalid signers JSON format")
    else:
        signers_list = signers

    # Add signed=false default
    for signer in signers_list:
        signer.setdefault("signed", False)
        signer.setdefault("order", 1)

    # Calculate expiry
    days = int(expiry_days) if expiry_days else (provider.default_expiry_days or 30)

    request_doc = frappe.get_doc({
        "doctype": "E-Signature Request",
        "contract": contract_name,
        "provider": provider_name,
        "status": "Draft",
        "signers": json.dumps(signers_list, ensure_ascii=False),
        "requested_by": frappe.session.user,
        "expiry_date": add_days(today(), days),
    })
    request_doc.insert(ignore_permissions=True)

    # Create log entry
    _create_log(request_doc.name, "Sent", event_date=now_datetime())

    # Simulate provider send (actual API call is a stub for now)
    envelope_id = _send_to_provider(provider, contract, request_doc)

    request_doc.db_set("status", "Sent")
    request_doc.db_set("sent_date", now_datetime())
    if envelope_id:
        request_doc.db_set("envelope_id", envelope_id)

    frappe.db.commit()

    return {
        "success": True,
        "signature_request": request_doc.name,
        "envelope_id": envelope_id,
        "expiry_date": str(request_doc.expiry_date),
    }


@frappe.whitelist()
def check_signature_status(signature_request_name=None, contract_name=None):
    """Check e-signature status from local DB.

    Args:
        signature_request_name: E-Signature Request document name
        contract_name: Contract name (finds latest request)
    """
    if not signature_request_name and not contract_name:
        frappe.throw("Either signature_request_name or contract_name is required")

    if not signature_request_name:
        requests = frappe.get_all(
            "E-Signature Request",
            filters={"contract": contract_name},
            fields=["name"],
            order_by="creation desc",
            limit=1,
        )
        if not requests:
            return {"success": True, "found": False, "message": "No signature request found"}
        signature_request_name = requests[0].name

    doc = frappe.get_doc("E-Signature Request", signature_request_name)

    # Get log entries
    logs = frappe.get_all(
        "E-Signature Log",
        filters={"signature_request": signature_request_name},
        fields=["event_type", "signer_email", "signer_name", "event_date"],
        order_by="event_date desc",
    )

    # Parse signers
    try:
        signers = json.loads(doc.signers) if doc.signers else []
    except json.JSONDecodeError:
        signers = []

    return {
        "success": True,
        "found": True,
        "signature_request": doc.name,
        "contract": doc.contract,
        "status": doc.status,
        "provider": doc.provider,
        "sent_date": str(doc.sent_date) if doc.sent_date else None,
        "completed_date": str(doc.completed_date) if doc.completed_date else None,
        "expiry_date": str(doc.expiry_date) if doc.expiry_date else None,
        "signers": signers,
        "logs": logs,
    }


@frappe.whitelist(allow_guest=True)
def callback_signature_complete():
    """Webhook callback for signature provider events.

    Expected JSON payload:
        envelope_id: Provider's envelope/document ID
        event_type: Sent/Viewed/Signed/Declined/Expired/Cancelled/Error
        signer_email: Email of the signer (optional)
        signer_name: Name of the signer (optional)
        ip_address: Signer's IP address (optional)
        certificate_data: Digital certificate data (optional)
        provider_event_id: Provider's unique event ID (optional)
    """
    data = frappe.request.get_json(silent=True) if frappe.request else {}
    if not data:
        frappe.throw("Invalid webhook payload")

    envelope_id = data.get("envelope_id")
    event_type = data.get("event_type")

    if not envelope_id or not event_type:
        frappe.throw("envelope_id and event_type are required")

    # Validate event_type against allowlist
    if event_type not in ALLOWED_EVENT_TYPES:
        frappe.logger("esignature").warning(
            f"Webhook rejected: invalid event_type '{event_type}' "
            f"for envelope_id '{envelope_id}' from {frappe.request.remote_addr if frappe.request else 'unknown'}"
        )
        frappe.throw(f"Invalid event_type: {event_type}")

    # Validate envelope_id exists in our DB (prevent forged callbacks)
    requests = frappe.get_all(
        "E-Signature Request",
        filters={"envelope_id": envelope_id},
        pluck="name",
        limit=1,
    )
    if not requests:
        frappe.logger("esignature").warning(
            f"Webhook rejected: unknown envelope_id '{envelope_id}' "
            f"from {frappe.request.remote_addr if frappe.request else 'unknown'}"
        )
        frappe.throw(f"No signature request found for envelope_id: {envelope_id}")

    # Audit log for all webhook events
    frappe.logger("esignature").info(
        f"Webhook received: event_type='{event_type}' envelope_id='{envelope_id}' "
        f"signer='{data.get('signer_email', '')}' "
        f"from={frappe.request.remote_addr if frappe.request else 'unknown'}"
    )

    request_name = requests[0]

    # Prevent duplicate events
    if data.get("provider_event_id"):
        if frappe.db.exists(
            "E-Signature Log",
            {"provider_event_id": data["provider_event_id"]},
        ):
            return {"success": True, "message": "Duplicate event ignored"}

    # Create log entry
    _create_log(
        request_name,
        event_type,
        signer_email=data.get("signer_email"),
        signer_name=data.get("signer_name"),
        event_date=now_datetime(),
        ip_address=data.get("ip_address"),
        certificate_data=data.get("certificate_data"),
        provider_event_id=data.get("provider_event_id"),
        raw_payload=json.dumps(data, ensure_ascii=False),
    )

    # Update request status based on event
    _update_request_status(request_name, event_type, data)

    frappe.db.commit()

    return {"success": True}


def _create_log(
    signature_request,
    event_type,
    signer_email=None,
    signer_name=None,
    event_date=None,
    ip_address=None,
    certificate_data=None,
    provider_event_id=None,
    raw_payload=None,
):
    """Create an E-Signature Log entry."""
    frappe.get_doc({
        "doctype": "E-Signature Log",
        "signature_request": signature_request,
        "event_type": event_type,
        "signer_email": signer_email,
        "signer_name": signer_name,
        "event_date": event_date or now_datetime(),
        "ip_address": ip_address,
        "certificate_data": certificate_data,
        "provider_event_id": provider_event_id,
        "raw_payload": raw_payload,
    }).insert(ignore_permissions=True)


def _update_request_status(request_name, event_type, data):
    """Update E-Signature Request status based on webhook event."""
    doc = frappe.get_doc("E-Signature Request", request_name)

    if event_type == "Signed":
        # Update signer status in JSON
        try:
            signers = json.loads(doc.signers) if doc.signers else []
            signer_email = data.get("signer_email")
            for signer in signers:
                if signer.get("email") == signer_email:
                    signer["signed"] = True
                    break
            doc.db_set("signers", json.dumps(signers, ensure_ascii=False))

            # Check if all signed
            all_signed = all(s.get("signed") for s in signers)
            if all_signed:
                doc.db_set("status", "Completed")
                doc.db_set("completed_date", now_datetime())
            else:
                doc.db_set("status", "Partially Signed")
        except json.JSONDecodeError:
            pass

    elif event_type == "Declined":
        doc.db_set("status", "Cancelled")
        doc.db_set("error_message", f"Declined by {data.get('signer_email', 'unknown')}")

    elif event_type == "Expired":
        doc.db_set("status", "Expired")

    elif event_type == "Cancelled":
        doc.db_set("status", "Cancelled")

    elif event_type == "Error":
        doc.db_set("error_message", data.get("error_message", "Unknown provider error"))


def _send_to_provider(provider, contract, request_doc):
    """Send signature request to provider (stub for future API integration).

    Returns envelope_id from provider, or a generated placeholder.
    """
    # Stub: actual CloudSign/DocuSign API calls will be implemented
    # when provider contracts are established.
    # For now, generate a placeholder envelope ID.
    import hashlib

    raw = f"{request_doc.name}-{provider.provider_type}-{now_datetime()}"
    envelope_id = hashlib.sha256(raw.encode()).hexdigest()[:32]
    return envelope_id
