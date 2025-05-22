import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_DIR = os.path.abspath(
    os.path.join(SCRIPT_DIR, "../../../src/ssb_dash_framework/modules")
)
OUT_DIR = SCRIPT_DIR

for filename in os.listdir(MODULE_DIR):
    if filename.endswith(".py") and filename != "__init__.py":
        modname = filename[:-3]
        rst_path = os.path.join(OUT_DIR, f"{modname}.rst")
        with open(rst_path, "w") as f:
            f.write(
                f"""{modname} module
{'=' * (len(modname) + 7)}

.. automodule:: ssb_dash_framework.modules.{modname}
   :members:
   :undoc-members:
   :show-inheritance:
"""
            )
