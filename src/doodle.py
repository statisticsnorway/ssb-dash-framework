import json
from ssb_dash_framework.utils.config_tools.yaml_parser import load_yaml
from ssb_dash_framework.experimental.modules.data_editor.data_view.data_view_custom import DataViewCustom
test = load_yaml("/home/onyxia/work/stat-naringer-dash/src/egentilpassing/skjemavisninger/ra_0255_skjemadata_foretak.yaml")

print(json.dumps(test[0], indent=2, ensure_ascii=False))
print()
print()


from ssb_dash_framework.utils.config_tools.parsed_config_models import parse_config_dict

parse_config_dict(test)