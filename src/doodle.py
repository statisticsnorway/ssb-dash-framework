import json
from ssb_dash_framework.utils.config_tools.yaml_parser import load_yaml
from ssb_dash_framework.experimental.modules.data_editor.data_view.data_view_custom import DataViewCustom, Layout
test = load_yaml("/home/onyxia/work/stat-naringer-dash/src/egentilpassing/skjemavisninger/ra_0255_skjemadata_foretak.yaml")

# print(json.dumps(test[0], indent=2, ensure_ascii=False))
# print()
# print()


# test_layout = [{
#   "type": "microlayout",
#   "label": "Omsetning og driftskostnad",
#   "form_data_table": "skjemadata_foretak",
#   "form_data_field_name_column": "variabel",
#   "layout": {
#     "type": "row",
#     "children": [
#       {
#         "type": "col",
#         "children": [
#           {
#             "type": "input",
#             "label": "totalOmsSkjema",
#             "field_settings": {
#               "field_path": "totalOmsSkjema",
#               "applies_to_tables": [
#                 "skjemadata_foretak"
#               ],
#               "applies_to_forms": [
#                 "RA-0255"
#               ]
#             }
#           }
#         ]
#       },
#       {
#         "type": "col",
#         "children": [
#           {
#             "type": "input",
#             "label": "totalDriftKostSkjema",
#             "field_settings": {
#               "field_path": "totalDriftKostSkjema",
#               "applies_to_tables": [
#                 "skjemadata_foretak"
#               ],
#               "applies_to_forms": [
#                 "RA-0255"
#               ]
#             }
#           }
#         ]
#       }
#     ]
#   }
# }]

# Layout(test_layout)

from ssb_dash_framework.utils.config_tools.parsed_config_models import parse_config_dict

print(
    parse_config_dict(test)
)