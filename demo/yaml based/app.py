import yaml
from pathlib import Path


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


def load_config(path: str | Path) -> dict:
    """Load a YAML config file, resolving any !include tags."""
    with open(path) as f:
        return yaml.load(f, Loader=IncludeLoader)


if __name__ == "__main__":
    import json

    config = load_config("/home/onyxia/work/ssb-dash-framework/demo/yaml based/main.yaml")
    print(json.dumps(config, indent=2, default=str))