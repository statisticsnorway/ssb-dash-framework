import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_BASE = os.path.abspath(os.path.join(SCRIPT_DIR, "../../src/ssb_dash_framework"))
OUT_BASE = SCRIPT_DIR

for subfolder in os.listdir(SRC_BASE):
    subfolder_path = os.path.join(SRC_BASE, subfolder)
    if not (
        os.path.isdir(subfolder_path)
        and os.path.isfile(os.path.join(subfolder_path, "__init__.py"))
    ):
        continue

    out_dir = os.path.join(OUT_BASE, subfolder)
    os.makedirs(out_dir, exist_ok=True)
    module_names = []

    for filename in os.listdir(subfolder_path):
        if filename.endswith(".py") and filename != "__init__.py":
            modname = filename[:-3]
            module_names.append(modname)
            rst_path = os.path.join(out_dir, f"{modname}.rst")
            with open(rst_path, "w") as f:
                f.write(
                    f"""{modname} module
{'=' * (len(modname) + 7)}

.. automodule:: ssb_dash_framework.{subfolder}.{modname}
   :members:
   :undoc-members:
   :show-inheritance:
"""
                )

    # Write or update index.rst with capitalized clickable links
    index_path = os.path.join(out_dir, "index.rst")
    with open(index_path, "w") as idx:
        idx.write(
            f"""{subfolder.capitalize()}
{'=' * len(subfolder)}

.. toctree::
   :maxdepth: 1
   :caption: {subfolder.capitalize()}

"""
        )
        for modname in sorted(module_names):
            idx.write(f"   {modname.capitalize()} <{modname}>\n")
