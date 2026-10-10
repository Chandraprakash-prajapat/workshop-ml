"""One place that says which role can use which MCP tool (RBAC).
Roles: user, super_admin  (system tools come later)."""


TOOL_ROLES = {
    # user (5)
    "doctor_details":    ["user", "super_admin"],
    "available_doctors": ["user", "super_admin"],
    "my_appointments":   ["user", "super_admin"],
    "my_prescriptions":  ["user"],
    "my_bills":          ["user"],
    # admin (3)
    "list_patients":     ["super_admin"],
    "all_appointments":  ["super_admin"],
    "pending_bills":     ["super_admin"],
    # system (2): AI ko kabhi nahi dikhte, sirf app khud chalata hai
    "system_health":     ["system"],
    "system_stats":      ["system"],
}


def tools_for(role):
    """Names of the tools this role may use."""
    return [name for name, roles in TOOL_ROLES.items() if role in roles]


def can_use(role, tool_name):
    """Unknown tool or unknown role means: no access."""
    return role in TOOL_ROLES.get(tool_name, [])