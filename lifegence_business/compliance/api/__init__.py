import frappe


@frappe.whitelist()
def has_compliance_access():
    """Check if current user has access to Compliance app.

    Only users with Compliance Manager or Compliance User role can access.
    General users will not see the app icon.
    """
    if frappe.session.user == "Administrator":
        return True

    user_roles = frappe.get_roles(frappe.session.user)

    # Only allow access if user has Compliance-specific roles
    compliance_roles = ["Compliance Manager", "Compliance User"]
    if any(role in user_roles for role in compliance_roles):
        return True

    # System Manager can also access for administration purposes
    if "System Manager" in user_roles:
        return True

    return False
