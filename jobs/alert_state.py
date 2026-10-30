"""Alert transitions independent of Spark and workspace clients."""


def resolving_keys(
    open_keys: set[tuple[str, str]],
    current_keys: set[tuple[str, str]],
    owned_rules: tuple[str, ...],
    evaluated_apps: set[str] | None = None,
) -> set[tuple[str, str]]:
    """Absence means cleared only within an emitter's successfully evaluated scope."""
    return {
        (rule, app)
        for rule, app in open_keys - current_keys
        if rule in owned_rules and (evaluated_apps is None or app in evaluated_apps)
    }
