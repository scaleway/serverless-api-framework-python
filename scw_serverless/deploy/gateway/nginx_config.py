from typing import NamedTuple, Union

from jinja2 import Environment, PackageLoader, select_autoescape

from scw_serverless.config.route import GatewayRoute, HTTPMethod

env = Environment(
    loader=PackageLoader("scw_serverless.deploy.gateway"),
    autoescape=select_autoescape(),
)


class _RoutingNode(NamedTuple):
    """Internal class used to generate the config."""

    path: str
    targets: Union[str, dict[HTTPMethod, str]]
    sublocations: "_RoutingTrie"


# Tree where the key is the route prefix
_RoutingTrie = dict[str, _RoutingNode]


class NginxConfigLocation(NamedTuple):
    """NginxConfigLocation used in the templates.

    :param path: Full path to match
    :param target: Proxy target, either a url or a map variable
    :param unallowed_methods: Methods that should return a 405
    :param sublocations: Children as sublocations to match
    """

    path: str
    target: str
    # This is used to generate a guard in the config to return a 405
    unallowed_methods: list[str]
    sublocations: list["NginxConfigLocation"]


class NginxConfigMethodsMap(NamedTuple):
    """NginxConfigMethodsMap used in the templates.

    :param var_name: Name of the generated map
    :param methods_to_targets: Targets depending on HTTP method
    """

    var_name: str
    methods_to_targets: dict[str, str]


def add_route_to_node(route: GatewayRoute, node: _RoutingNode) -> None:
    """Add a single route to the tree."""
    assert route.target  # For typing purposes only
    path = route.path.split("/")
    current_node = node

    # Traverse the tree to find the node on which to add our route
    for prefix in path[:-1]:
        if prefix == "" or prefix.isspace():
            continue
        if prefix not in current_node.sublocations:
            node = _RoutingNode(path="", targets={}, sublocations={})
            current_node.sublocations[prefix] = node
            current_node = node
        else:
            current_node = current_node.sublocations[prefix]
    prefix = path[-1]
    # Add the route to the correct node
    if prefix not in current_node.sublocations:
        targets = route.target
        if route.methods:
            targets = {method: route.target for method in route.methods}
        current_node.sublocations[prefix] = _RoutingNode(
            path=route.path, targets=targets, sublocations={}
        )
    else:
        # We need to merge the route with an existing one
        targets = current_node.sublocations[prefix].targets
        if isinstance(targets, str) or not route.methods:
            # Unlikely to occur as methods = None are mostly used for compatibility
            raise ValueError(
                f"Could not merge route: {route} with existing target: {targets}"
            )
        for method in route.methods:
            if method in targets:
                raise ValueError(
                    f"{method} in route {route} already bound to {targets[method]}"
                )
            targets[method] = route.target


def build_routing_trie(routes: list[GatewayRoute]) -> _RoutingTrie:
    """Generate a location prefix tree given the configured routes."""
    root: _RoutingTrie = {"/": _RoutingNode(path="/", targets={}, sublocations={})}
    for route in routes:
        node = root["/"]
        add_route_to_node(route, node)
    return root


def generate_config_from_trie(
    trie: _RoutingTrie,
) -> tuple[list[NginxConfigLocation], list[NginxConfigMethodsMap]]:
    """Generates the data structure used in the template."""
    if not trie:
        return ([], [])
    locations = []
    method_maps = []
    for _, node in trie.items():
        locs, maps = generate_config_from_trie(node.sublocations)
        method_maps.extend(maps)
        if not node.targets:
            # If a route doesn't define a target we raise its children
            locations.extend(locs)
            continue
        target = None
        unallowed_methods = []
        if isinstance(node.targets, str):
            target = node.targets
        elif len(node.targets) == 1:
            (method, target), *_ = node.targets.items()
            unallowed_methods = [m.value for m in HTTPMethod if m != method]
        else:
            # Target will be bound to a map that assign depending on the method
            var_name = f'${node.path.replace("/", "_").lstrip("_")}_target'
            target = var_name
            unallowed_methods = [
                method.value for method in HTTPMethod if method not in node.targets
            ]
            method_maps.append(
                NginxConfigMethodsMap(
                    var_name=var_name,
                    methods_to_targets={
                        method.value: target for method, target in node.targets.items()
                    },
                )
            )
        locations.append(
            NginxConfigLocation(
                path=node.path,
                target=target,
                unallowed_methods=unallowed_methods,
                sublocations=locs,
            )
        )

    return locations, method_maps


def generate_nginx_config(routes: list[GatewayRoute]) -> str:
    """Generates a Nginx reverse-proxy config for the gateway."""
    for route in routes:
        route.validate()

    trie = build_routing_trie(routes)

    locations, method_maps = generate_config_from_trie(trie)

    template = env.get_template("nginx.conf.jinja2")
    return template.render(locations=locations, method_maps=method_maps)
