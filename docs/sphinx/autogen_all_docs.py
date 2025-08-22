import ast
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_BASE = os.path.abspath(os.path.join(SCRIPT_DIR, "../../src/ssb_dash_framework"))
OUT_BASE = SCRIPT_DIR


def extract_docstring(pyfile):
    """Extract the top-level docstring from a Python file."""
    with open(pyfile, encoding="utf-8") as f:
        node = ast.parse(f.read())
        return ast.get_docstring(node) or ""


for root, dirs, files in os.walk(SRC_BASE):
    if "__init__.py" not in files:
        continue  # Not a package

    rel_path = os.path.relpath(root, SRC_BASE)
    out_dir = os.path.join(OUT_BASE, rel_path)
    os.makedirs(out_dir, exist_ok=True)
    module_names = []
    subpackage_names = []

    # Find subpackages (directories with __init__.py)
    for d in dirs:
        sub_init = os.path.join(root, d, "__init__.py")
        if os.path.isfile(sub_init):
            subpackage_names.append(d)

    for filename in files:
        if filename.endswith(".py") and filename != "__init__.py":
            modname = filename[:-3]
            module_names.append(modname)
            # Build the full module path for automodule
            if rel_path == ".":
                module_path = f"ssb_dash_framework.{modname}"
            else:
                dotted = rel_path.replace(os.sep, ".")
                module_path = f"ssb_dash_framework.{dotted}.{modname}"
            rst_path = os.path.join(out_dir, f"{modname}.rst")
            with open(rst_path, "w") as f:
                f.write(
                    f"""{modname} module
{'=' * (len(modname) + 7)}

.. automodule:: {module_path}
   :members:
   :undoc-members:
   :show-inheritance:
"""
                )

    # Extract docstring from __init__.py
    init_path = os.path.join(root, "__init__.py")
    docstring = extract_docstring(init_path)
    docstring_section = f"{docstring}\n\n" if docstring else ""

    # Write or update index.rst with docstring and clickable links for modules and subpackages
    index_path = os.path.join(out_dir, "index.rst")
    package_name = os.path.basename(root)
    with open(index_path, "w") as idx:
        idx.write(
            f"""{package_name.capitalize()}
{'=' * len(package_name)}

{docstring_section}.. toctree::
   :maxdepth: 1
   :caption: {package_name.capitalize()}

"""
        )
        for modname in sorted(module_names):
            idx.write(f"   {modname.capitalize()} <{modname}>\n")
        for subpkg in sorted(subpackage_names):
            idx.write(f"   {subpkg.replace('_', ' ').capitalize()} <{subpkg}/index>\n")
