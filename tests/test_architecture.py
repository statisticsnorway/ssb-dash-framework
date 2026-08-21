"""Here we test compliance with architecture decisions outlined in docs/architecture.md where possible."""

import ast
from pathlib import Path

PACKAGE_NAME = "ssb_dash_framework"
ROOT = Path("src") / PACKAGE_NAME
MODULES = ROOT / "modules"
PREFIX = "ssb_dash_framework.modules."
PACKAGE = PREFIX.rstrip(".")  # "ssb_dash_framework.modules"
AGGREGATOR_INIT = MODULES / "__init__.py"
EXPERIMENTAL = ROOT / "experimental"
EXPERIMENTAL_PREFIX = f"{PACKAGE_NAME}.experimental"


def resolve_import(path: Path, node: ast.AST) -> list[str]:
    """Return the list of fully-dotted module names a node imports,
    resolving relative (`from . import x`) imports using the file's
    location on disk."""
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]

    if not isinstance(node, ast.ImportFrom):
        return []

    if node.level == 0:
        return [node.module or ""]

    package_parts = list(path.parent.relative_to(ROOT.parent).parts)
    hops = node.level - 1
    package_parts = (
        package_parts[: len(package_parts) - hops] if hops else package_parts
    )

    if node.module:
        package_parts = package_parts + node.module.split(".")

    return [".".join(package_parts)]


def build_export_map() -> dict[str, str]:
    """Scan modules/__init__.py and map each re-exported name to the
    submodule it actually comes from, e.g. {'AarsregnskapTab': 'aarsregnskap'}."""
    export_map: dict[str, str] = {}
    tree = ast.parse(AGGREGATOR_INIT.read_text())

    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue

        for resolved in resolve_import(AGGREGATOR_INIT, node):
            if not resolved.startswith(PREFIX):
                continue
            source_module = resolved[len(PREFIX) :].split(".")[0]
            for alias in node.names:
                if alias.name == "*":
                    # Can't statically resolve star-imports; if the
                    # aggregator ever does this, extend this function
                    # instead of silently trusting it.
                    raise NotImplementedError(
                        f"{AGGREGATOR_INIT} uses a wildcard import from "
                        f"{resolved!r}; build_export_map() can't resolve "
                        "re-exported names statically."
                    )
                exported_name = alias.asname or alias.name
                export_map[exported_name] = source_module

    return export_map


def module_files(module_unit: Path):
    if module_unit.is_dir():
        yield from module_unit.rglob("*.py")
    else:
        yield module_unit


def test_modules_are_independent():
    export_map = build_export_map()

    for module_unit in MODULES.iterdir():
        if module_unit.suffix not in ("", ".py"):
            continue
        module_name = module_unit.stem

        for path in module_files(module_unit):
            if path == AGGREGATOR_INIT:
                continue

            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                # Case 1: `from ssb_dash_framework.modules.X import Y`
                for name in resolve_import(path, node):
                    if name.startswith(PREFIX):
                        imported_module = name[len(PREFIX) :].split(".")[0]
                        assert (
                            imported_module == module_name
                        ), f"{path} imports {PREFIX}{imported_module}"

                # Case 2: `from ssb_dash_framework.modules import Y`
                # (Y re-exported via the aggregator __init__.py)
                if isinstance(node, ast.ImportFrom):
                    for resolved in resolve_import(path, node):
                        if resolved != PACKAGE:
                            continue
                        for alias in node.names:
                            source_module = export_map.get(alias.name)
                            if source_module is None:
                                continue  # not something the aggregator re-exports
                            assert source_module == module_name, (
                                f"{path} imports {alias.name} "
                                f"(from {PREFIX}{source_module}) via the "
                                f"{PACKAGE} aggregator"
                            )


def is_experimental_import(name: str) -> bool:
    return name == EXPERIMENTAL_PREFIX or name.startswith(EXPERIMENTAL_PREFIX + ".")


def test_experimental_is_not_imported_from_top_level():
    for path in ROOT.rglob("*.py"):
        # Skip experimental/ itself — code in there is allowed to
        # import from its own package freely.
        if path == EXPERIMENTAL or EXPERIMENTAL in path.parents:
            continue

        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            for name in resolve_import(path, node):
                assert not is_experimental_import(name), (
                    f"{path} imports {name!r} — nothing outside "
                    f"{EXPERIMENTAL_PREFIX} may import from experimental/"
                )
