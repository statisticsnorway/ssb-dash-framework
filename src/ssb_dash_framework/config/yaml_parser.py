import yaml

# TODO: Add an !include loader thing


def config_parser_yaml(path: str):
    with open(path) as f:
        return yaml.safe_load(f)
