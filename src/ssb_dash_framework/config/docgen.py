"""Generate a markdown reference of every class that can be configured through yaml.

Run from the repository root to (re)generate the reference::

    python -m ssb_dash_framework.config.docgen
    python -m ssb_dash_framework.config.docgen --check  # exit 1 if outdated

The script only uses absolute imports, so it can be moved anywhere in the repository.
"""

import argparse
import importlib
import inspect
import logging
import pkgutil
import re
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from pydantic import BaseModel

import ssb_dash_framework
from ssb_dash_framework.config.models import YamlLoadable
from ssb_dash_framework.config.models import get_module_registry

logger = logging.getLogger(__name__)

PACKAGE = ssb_dash_framework
OUTPUT_RELATIVE_PATH = Path("docs") / "yaml_reference.md"
REGENERATE_COMMAND = "python -m ssb_dash_framework.config.docgen"

# Removed by YamlLoadable.from_yaml, the placement in the config decides these.
DEFAULT_FROM_YAML_IGNORED_ARGS = {"as_type", "window_scrollable"}

INTRO = """\
# YAML configuration reference

An app can be configured with a yaml file instead of Python code. This page lists
every class that can be created from yaml, and which arguments each class accepts.

## Key concepts

**Yaml maps 1-to-1 onto Python arguments.** Every key in a yaml block is passed as a
keyword argument with the same name to the class constructor (`__init__`). If you
know how to create a class in Python, you know how to configure it in yaml, and the
other way around. These two are equivalent:

```python
FreeSearch(conn=None)
```

```yaml
- type: FreeSearch
  conn: null
```

**`type` selects the class.** The value of `type` must match the class name exactly.
All other keys in the block become arguments. Unknown keys are rejected with an
error listing the valid arguments.

**The app config file.** The root of an app config has two sections:

```yaml
app_settings:          # Arguments to app_setup(), and the variable selector config
  port: 8070
  variableselector:
    ident: ident
modules:
  tabs:                # Modules shown as tabs
    - type: SomeModule
  windows:             # Modules shown as windows (modals) opened from the sidebar
    - type: OtherModule
```

Whether a module is a tab or a window is decided by which list it is placed in, so
`as_type` should not be set in yaml.

**Nested classes.** Some arguments expect other configurable classes. These are
written as nested blocks with their own `type` key, following the same rules.

**Splitting files.** Use `!include path/to/file.yaml` to insert the content of another
yaml file. Relative paths are resolved from the folder of the including file.

**Custom `from_yaml`.** Most classes use the default loader, which passes the yaml
keys straight to the constructor. Some classes need to build objects from the yaml
before calling the constructor, and define their own `from_yaml`. This is noted in
the class section below, and the expected structure may differ from the
constructor arguments listed.
"""


def find_repo_root() -> Path:
    """Find the repository root by searching upwards for pyproject.toml.

    Returns:
        The repository root, or the current working directory if none is found.
    """
    for start in (Path(__file__).resolve(), Path.cwd().resolve()):
        for candidate in (start, *start.parents):
            if (candidate / "pyproject.toml").is_file():
                return candidate
    return Path.cwd()


def default_output_path() -> Path:
    """Path to the generated markdown file.

    Returns:
        The absolute path of the markdown file.
    """
    return find_repo_root() / OUTPUT_RELATIVE_PATH


def import_all_modules() -> None:
    """Import all submodules so every YamlLoadable subclass registers itself."""
    for info in pkgutil.walk_packages(PACKAGE.__path__, f"{PACKAGE.__name__}."):
        if info.name.rsplit(".", 1)[-1] == "__main__":
            continue
        try:
            importlib.import_module(info.name)
        except Exception as e:
            logger.warning(f"Skipping '{info.name}', import failed: {e!r}")


def _in_package(module_name: str) -> bool:
    return module_name == PACKAGE.__name__ or module_name.startswith(
        f"{PACKAGE.__name__}."
    )


def _package_modules() -> Iterator[Any]:
    for name, module in sorted(sys.modules.items()):
        if module is not None and _in_package(name):
            yield module


def collect_classes() -> list[type]:
    """Find all concrete classes that can be created through a from_yaml method.

    Returns:
        The classes, sorted by module and name.
    """
    import_all_modules()
    found: set[type] = {registered.type for registered in get_module_registry()}
    for module in _package_modules():
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if _in_package(obj.__module__) and "from_yaml" in vars(obj):
                found.add(obj)
    found.discard(YamlLoadable)
    # The registry also holds classes defined outside the package, e.g. in tests.
    return sorted(
        (
            cls
            for cls in found
            if not inspect.isabstract(cls) and _in_package(cls.__module__)
        ),
        key=lambda cls: (cls.__module__, cls.__name__),
    )


def from_yaml_owner(cls: type) -> type | None:
    """Return the class defining a custom from_yaml, or None if the default is used.

    Args:
        cls: The class to inspect.

    Returns:
        The class in the MRO that defines from_yaml, unless it is YamlLoadable.
    """
    for base in cls.__mro__:
        if "from_yaml" in vars(base):
            return None if base is YamlLoadable else base
    return None


def parse_args_section(docstring: str | None) -> dict[str, str]:
    """Extract argument descriptions from a Google style docstring.

    Args:
        docstring: The cleaned docstring.

    Returns:
        Mapping from argument name to its description.
    """
    descriptions: dict[str, str] = {}
    in_args = False
    current: str | None = None
    indent: int | None = None
    for line in (docstring or "").splitlines():
        stripped = line.strip()
        if stripped in ("Args:", "Arguments:", "Parameters:"):
            in_args = True
            continue
        if not in_args or not stripped:
            continue
        if not line.startswith((" ", "\t")):
            break
        match = re.match(r"^(\s+)\*{0,2}(\w+)(?:\s*\(.*?\))?:\s*(.*)$", line)
        if match and (indent is None or len(match.group(1)) == indent):
            indent = len(match.group(1))
            current = match.group(2)
            descriptions[current] = match.group(3)
        elif current is not None:
            descriptions[current] = f"{descriptions[current]} {stripped}".strip()
    return descriptions


def first_paragraph(docstring: str | None) -> str:
    """Return the first paragraph of a docstring as a single line.

    Args:
        docstring: The cleaned docstring.

    Returns:
        The first paragraph, or an empty string.
    """
    if not docstring:
        return ""
    return " ".join(docstring.strip().split("\n\n")[0].split())


def format_annotation(annotation: Any) -> str:
    """Format a type annotation as short readable text.

    Args:
        annotation: The annotation to format.

    Returns:
        The annotation without module prefixes, or an empty string if missing.
    """
    if annotation is inspect.Parameter.empty:
        return ""
    if isinstance(annotation, str):
        text = annotation
    elif isinstance(annotation, type):
        text = annotation.__qualname__
    else:
        text = inspect.formatannotation(annotation)
    return re.sub(r"\b(?:\w+\.)+(\w+)", r"\1", text)


def format_default(value: Any) -> str:
    """Format a default value for the documentation.

    Args:
        value: The default value.

    Returns:
        The repr of the value, or the type name if the repr is not stable.
    """
    text = repr(value)
    if " at 0x" in text:
        return f"<{type(value).__name__}>"
    return text


def _cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def describe_parameters(cls: type) -> tuple[list[tuple[str, str, str, str]], bool]:
    """Describe the arguments that can be set in yaml for a class.

    Args:
        cls: The class to describe.

    Returns:
        Rows of (name, type, default, description), and whether extra keyword
        arguments are accepted.
    """
    rows: list[tuple[str, str, str, str]] = []
    if issubclass(cls, BaseModel):
        for name, field in cls.model_fields.items():
            default = (
                "required"
                if field.is_required()
                else f"`{format_default(field.get_default(call_default_factory=False))}`"
            )
            rows.append(
                (
                    name,
                    format_annotation(field.annotation),
                    default,
                    field.description or "",
                )
            )
        return rows, cls.model_config.get("extra") == "allow"

    init = vars(cls).get("__init__") or cls.__init__
    descriptions = {
        **parse_args_section(inspect.getdoc(cls)),
        **parse_args_section(inspect.getdoc(init)),
    }
    ignored = DEFAULT_FROM_YAML_IGNORED_ARGS if from_yaml_owner(cls) is None else set()
    accepts_kwargs = False
    parameters = list(inspect.signature(cls.__init__).parameters.values())[1:]
    for param in parameters:
        if param.kind is param.VAR_KEYWORD:
            accepts_kwargs = True
            continue
        if (
            param.kind is param.VAR_POSITIONAL
            or param.name in ignored
            or param.name.startswith("_")
        ):
            continue
        default = (
            "required"
            if param.default is param.empty
            else f"`{format_default(param.default)}`"
        )
        rows.append(
            (
                param.name,
                format_annotation(param.annotation),
                default,
                descriptions.get(param.name, ""),
            )
        )
    return rows, accepts_kwargs


def render_class(cls: type) -> str:
    """Render the markdown section for a single class.

    Args:
        cls: The class to document.

    Returns:
        The markdown section.
    """
    is_registered = issubclass(cls, YamlLoadable)
    lines = [f"## {cls.__name__}", ""]
    if cls.__module__.startswith(f"{PACKAGE.__name__}.experimental"):
        lines += ["> **Experimental:** may change without notice.", ""]
    lines += [f"Import path: `{cls.__module__}.{cls.__name__}`", ""]

    summary = first_paragraph(inspect.cleandoc(vars(cls).get("__doc__") or ""))
    if summary:
        lines += [summary, ""]

    if not is_registered:
        lines += [
            f"Not selected with `type`. Created with `{cls.__name__}.from_yaml(...)`"
            " or from the matching section of the app config.",
            "",
        ]

    owner = from_yaml_owner(cls)
    if owner is not None:
        method = vars(owner)["from_yaml"].__func__
        signature = (
            str(inspect.signature(method)).replace("(cls, ", "(").replace("(cls)", "()")
        )
        inherited = "" if owner is cls else f", inherited from `{owner.__name__}`"
        lines += [f"**Custom loader:** `from_yaml{signature}`{inherited}.", ""]
        loader_summary = first_paragraph(inspect.getdoc(method))
        if loader_summary:
            lines += [loader_summary, ""]

    rows, accepts_kwargs = describe_parameters(cls)
    if rows:
        lines += [
            "| Argument | Type | Default | Description |",
            "| --- | --- | --- | --- |",
        ]
        lines += [
            f"| `{name}` | {_cell(f'`{type_}`' if type_ else '')} | {_cell(default)}"
            f" | {_cell(description)} |"
            for name, type_, default, description in rows
        ]
        lines.append("")
    else:
        lines += ["Takes no arguments.", ""]
    if accepts_kwargs:
        lines += ["Additional keyword arguments are accepted.", ""]

    example = [f"- type: {cls.__name__}"] if is_registered else []
    indent = "  " if is_registered else ""
    example += [
        f"{indent}{name}: <{name}>"
        for name, _, default, _ in rows
        if default == "required"
    ]
    if example:
        lines += ["```yaml", *example, "```", ""]
    return "\n".join(lines)


def render() -> str:
    """Render the full markdown reference.

    Returns:
        The markdown content.
    """
    classes = collect_classes()
    lines = [
        INTRO,
        f"<!-- Auto-generated. Do not edit, regenerate with `{REGENERATE_COMMAND}`. -->",
        "",
        "## Contents",
        "",
        *(f"- [{cls.__name__}](#{cls.__name__.lower()})" for cls in classes),
        "",
        *(render_class(cls) for cls in classes),
    ]
    text = "\n".join(line.rstrip() for line in "\n".join(lines).splitlines())
    return text.rstrip("\n") + "\n"


def main(argv: list[str] | None = None) -> int:
    """Write the reference, or check that it is up to date.

    Args:
        argv: Command line arguments.

    Returns:
        The exit code.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit with code 1 if the file is outdated instead of writing it.",
    )
    args = parser.parse_args(argv)
    output: Path = args.output or default_output_path()
    content = render()

    if args.check:
        current = output.read_text(encoding="utf-8") if output.exists() else ""
        if current != content:
            print(f"{output} is outdated. Run `{REGENERATE_COMMAND}`.")
            return 1
        print(f"{output} is up to date.")
        return 0

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
