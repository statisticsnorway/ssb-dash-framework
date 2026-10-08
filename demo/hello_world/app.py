import os

from hello_module import HelloModule
from hello_module import HelloModuleDataHandlerCat
from hello_module import HelloModuleDataHandlerDefault

from ssb_dash_framework import VariableSelectorConfig
from ssb_dash_framework import app_setup
from ssb_dash_framework import main_layout

VariableSelectorConfig(refnr="Refnr")

port = 8070
service_prefix = os.getenv("JUPYTERHUB_SERVICE_PREFIX", "/")
domain = os.getenv("JUPYTERHUB_HTTP_REFERER", None)
app = app_setup(port, service_prefix, "lumen", logging_level="debug", log_to_file=True)

tab_list = []

tab_list.append(
    HelloModule(label="Default", data_handler=HelloModuleDataHandlerDefault())
)

tab_list.append(HelloModule(label="Cat", data_handler=HelloModuleDataHandlerCat()))

window_list = []

app.layout = main_layout(window_list, tab_list)

if __name__ == "__main__":
    app.run(debug=False, port=port, jupyter_server_url=domain, jupyter_mode="tab")
