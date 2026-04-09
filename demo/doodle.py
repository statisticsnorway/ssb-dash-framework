from pathlib import Path

import yaml

from ssb_dash_framework.modules.building_blocks.microlayout_components.models import Col
from ssb_dash_framework.modules.building_blocks.microlayout_components.models import (
    EditableField,
)
from ssb_dash_framework.modules.building_blocks.microlayout_components.models import (
    InputField,
)
from ssb_dash_framework.modules.building_blocks.microlayout_components.models import (
    Layout,
)
from ssb_dash_framework.modules.building_blocks.microlayout_components.models import (
    Node,
)
from ssb_dash_framework.modules.building_blocks.microlayout_components.models import Row


class IncludeLoader(yaml.SafeLoader):
    """YAML loader that supports !include tags for file splitting."""

    def __init__(self, stream):
        self._root = Path(stream.name).parent
        super().__init__(stream)


def _include_constructor(loader: IncludeLoader, node: yaml.Node):
    include_path = loader._root / loader.construct_scalar(node)

    with open(include_path) as f:
        return yaml.load(f, Loader=IncludeLoader)


IncludeLoader.add_constructor("!include", _include_constructor)


def config_parser_yaml(path: str | Path) -> dict:
    """Load a YAML config file, resolving any !include tags."""
    with open(path) as f:
        config = yaml.load(f, Loader=IncludeLoader)

    return config


target = [
    {
        "type": "row",
        "children": [
            {
                "type": "col",
                "children": [
                    {
                        "type": "input",
                        "label": "Totalareal",
                        "field_settings": {"field_path": "totalareal"},
                    },
                    {
                        "type": "input",
                        "label": "Fulldyrket",
                        "field_settings": {"field_path": "fulldyrket"},
                    },
                ],
            },
            {
                "type": "col",
                "children": [
                    {
                        "type": "input",
                        "label": "Innmarksbeite",
                        "field_settings": {"field_path": "innmarksbeite"},
                    }
                ],
            },
        ],
    }
]

from typing import Any


def build_node_from_dict(d: dict[str, Any]) -> Node:
    """Recursively build a Node from a dictionary."""
    # Handle container nodes first
    if "row" in d:
        children = [build_node_from_dict(child) for child in d["row"]]
        return Row(type="row", children=children)
    elif "col" in d:
        children = [build_node_from_dict(child) for child in d["col"]]
        return Col(type="col", children=children)

    # Handle input fields (you can extend this for other leaf types)
    elif d.get("type") == "input":
        field_path = d.get("field_path", "")
        # Create a dummy EditableField — replace with your real settings as needed
        field_settings = EditableField(field_path=field_path)
        return InputField(
            type="input",
            label=d.get("label", ""),
            value=d.get("value", ""),
            field_settings=field_settings,
        )

    else:
        raise ValueError(f"Unsupported node type: {d}")


def build_layout_from_list(data: list[dict[str, Any]]) -> Layout:
    """Build a Layout object from a list of node dicts."""
    nodes = [build_node_from_dict(d) for d in data]
    # Convert nodes to serializable dicts for Layout initialization
    node_dicts = [node.model_dump() for node in nodes]
    return Layout(node_dicts)


if __name__ == "__main__":

    Layout(target)

    import json

    config = config_parser_yaml("/home/onyxia/work/ssb-dash-framework/demo/demo.yaml")
    print(json.dumps(config["microlayout"]["layout"], indent=2, default=str))
    print("-----------------")

    layout = list()

    print(config["microlayout"]["layout"])

    layout = build_layout_from_list(config["microlayout"]["layout"])

    print(layout)
