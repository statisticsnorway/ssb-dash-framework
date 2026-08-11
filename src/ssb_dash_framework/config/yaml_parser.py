from pathlib import Path

import yaml


def _build_yaml_loader(base_path: Path) -> type:
    class CustomLoader(yaml.SafeLoader):
        pass

    def include_constructor(loader, node):
        include_path = Path(loader.construct_scalar(node))
        if not include_path.is_absolute():
            include_path = base_path / include_path
        with open(include_path) as f:
            return yaml.load(f, Loader=_build_yaml_loader(include_path.parent))

    CustomLoader.add_constructor("!include", include_constructor)
    return CustomLoader


def config_parser_yaml(path: str) -> dict:
    path = Path(path)
    with open(path) as f:
        return yaml.load(f, Loader=_build_yaml_loader(path.parent))
