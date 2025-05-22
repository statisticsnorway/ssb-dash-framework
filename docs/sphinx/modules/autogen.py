import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_DIR = os.path.abspath(
    os.path.join(SCRIPT_DIR, "../../../src/ssb_dash_framework/modules")
)
OUT_DIR = SCRIPT_DIR

module_names = []

for filename in os.listdir(MODULE_DIR):
    if filename.endswith(".py") and filename != "__init__.py":
        modname = filename[:-3]
        module_names.append(modname)
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

# Write or update index.rst with capitalized clickable links
index_path = os.path.join(OUT_DIR, "index.rst")
with open(index_path, "w") as idx:
    idx.write("""Modules
=======

.. toctree::
   :maxdepth: 1
   :caption: Modules

""")
    for modname in sorted(module_names):
        idx.write(f"   {modname.capitalize()} <{modname}>\n")
