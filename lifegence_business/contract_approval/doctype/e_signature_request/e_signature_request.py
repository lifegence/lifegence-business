import json

import frappe
from frappe.model.document import Document
from frappe.utils import add_days, now_datetime, today


class ESignatureRequest(Document):
    def validate(self):
        self._validate_contract_status()
        self._validate_signers()
        self._validate_no_duplicate()
        self._set_defaults()

    def _validate_contract_status(self):
        contract_status = frappe.db.get_value("Contract", self.contract, "status")
        if contract_status not in ("Approved", "Active"):
            frappe.throw("E-Signature requests can only be created for Approved or Active contracts")

    def _validate_signers(self):
        try:
            signers = json.loads(self.signers)
        except (json.JSONDecodeError, TypeError):
            frappe.throw("Signers must be a valid JSON array")

        if not isinstance(signers, list) or len(signers) == 0:
            frappe.throw("At least one signer is required")

        for signer in signers:
            if not isinstance(signer, dict):
                frappe.throw("Each signer must be a JSON object")
            if not signer.get("name") or not signer.get("email"):
                frappe.throw("Each signer must have 'name' and 'email' fields")

    def _validate_no_duplicate(self):
        if self.is_new():
            existing = frappe.db.exists(
                "E-Signature Request",
                {
                    "contract": self.contract,
                    "status": ["in", ["Draft", "Sent", "Partially Signed"]],
                },
            )
            if existing:
                frappe.throw(
                    f"An active signature request already exists for this contract: {existing}"
                )

    def _set_defaults(self):
        if not self.requested_by:
            self.requested_by = frappe.session.user
        if not self.expiry_date:
            provider = frappe.get_doc("E-Signature Provider Settings", self.provider)
            self.expiry_date = add_days(today(), provider.default_expiry_days or 30)
