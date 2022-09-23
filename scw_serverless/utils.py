def module_to_path(module: str) -> str:
    """
    Replace dots by slash in the module name

    :param module:
    :return:
    """
    return module.replace(
        ".", "/"
    )  # This may break in certain scenarios need to test it. For example if your
    # serverless framework is not at the root of you project.


def to_camel_case(snake_str: str) -> str:
    components = snake_str.split("_")
    # We capitalize the first letter of each component except the first one
    # with the 'title' method and join them together.
    return components[0] + "".join(x.title() for x in components[1:])


def to_valid_fn_name(name: str) -> str:
    return name.replace("_", "-")
