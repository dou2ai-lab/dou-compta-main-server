# -----------------------------------------------------------------------------
# File: roles.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Description: PRD role names and helpers for RBAC (Employee, Approver, Finance, Admin)
# -----------------------------------------------------------------------------

"""
PRD roles: Employee, Approver, Finance, Admin.
Stored in DB as lowercase: employee, approver, finance, admin.
"""

# Canonical role names (lowercase, as stored in DB)
ROLE_ADMIN = "admin"
ROLE_EMPLOYEE = "employee"
ROLE_APPROVER = "approver"
ROLE_FINANCE = "finance"

# All PRD roles in display order
PRD_ROLES = (ROLE_ADMIN, ROLE_EMPLOYEE, ROLE_APPROVER, ROLE_FINANCE)

# Role assigned to new signups
DEFAULT_SIGNUP_ROLE = ROLE_EMPLOYEE


def has_admin_role(role_names: list) -> bool:
    """True if the user has the admin role (case-insensitive)."""
    if not role_names:
        return False
    return any(r and str(r).lower() == ROLE_ADMIN for r in role_names)


# Canonical RBAC helpers (requested names)
def is_admin(user_roles: list) -> bool:
    """True if the user has the admin role."""
    return has_admin_role(user_roles)


def has_approver_role(role_names: list) -> bool:
    """True if the user has approver or admin role."""
    if not role_names:
        return False
    lower = [str(r).lower() for r in role_names if r]
    return ROLE_ADMIN in lower or ROLE_APPROVER in lower


def has_finance_role(role_names: list) -> bool:
    """True if the user has finance or admin role."""
    if not role_names:
        return False
    lower = [str(r).lower() for r in role_names if r]
    return ROLE_ADMIN in lower or ROLE_FINANCE in lower


def can_approve_expense(role_names: list) -> bool:
    """True if the user can approve expenses (admin, approver, or finance)."""
    if not role_names:
        return False
    lower = [str(r).lower() for r in role_names if r]
    return ROLE_ADMIN in lower or ROLE_APPROVER in lower or ROLE_FINANCE in lower


def can_approve(user_roles: list) -> bool:
    """True if the user can approve (admin/approver/finance)."""
    return can_approve_expense(user_roles)


def can_view_approvals(user_roles: list) -> bool:
    """
    In this system, "view approvals" is aligned with "can approve":
    approver/finance/admin can view pending approval queues.
    """
    return can_approve_expense(user_roles)
