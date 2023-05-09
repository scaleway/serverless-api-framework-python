def module_to_path(module: str) -> str:
    """Replaces dots by slash in the module name."""
    return module.replace(
        ".", "/"
    )  # This may break in certain scenarios need to test it. For example if your
    # serverless framework is not at the root of you project.


def to_valid_function_name(name: str) -> str:
    """Converts underscores in snake case to dashes."""
    return name.lower().replace("_", "-")
