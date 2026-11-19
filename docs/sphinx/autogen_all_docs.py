"""Generate the API reference .rst files for every package in src/ssb_dash_framework.

Run with `uv run docs/sphinx/autogen_all_docs.py` after adding, removing or renaming modules.

Every package gets an index.rst and every module gets a <module>.rst. The root package
gets api.rst instead of index.rst, so it does not clash with index.md. Any .rst file
that was not written by this run is deleted, so removed modules disappear from the docs.
"""

import ast
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_BASE = os.path.abspath(os.path.join(SCRIPT_DIR, "../../src/ssb_dash_framework"))
OUT_BASE = SCRIPT_DIR
SKIP_DIRS = {"_build", "templates", "docs"}


def extract_docstring(pyfile: str) -> str:
    """Extract the top-level docstring from a Python file."""
    with open(pyfile, encoding="utf-8") as f:
        node = ast.parse(f.read())
        return ast.get_docstring(node) or ""


written: set[str] = set()

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
            written.add(os.path.normpath(rst_path))
            with open(rst_path, "w") as f:
                f.write(f"""{modname} module
{'=' * (len(modname) + 7)}

.. automodule:: {module_path}
   :members:
   :undoc-members:
   :show-inheritance:
""")

    # Extract docstring from __init__.py
    init_path = os.path.join(root, "__init__.py")
    docstring = extract_docstring(init_path)
    docstring_section = f"{docstring}\n\n" if docstring else ""

    # Write or update index.rst with docstring and clickable links for modules and subpackages
    if rel_path == ".":
        index_path = os.path.join(out_dir, "api.rst")
        title = "API reference"
    else:
        index_path = os.path.join(out_dir, "index.rst")
        title = os.path.basename(root).capitalize()
    written.add(os.path.normpath(index_path))
    with open(index_path, "w") as idx:
        idx.write(f"""{title}
{'=' * len(title)}

{docstring_section}.. toctree::
   :maxdepth: 1
   :caption: {title}

""")
        # Write subpackages first
        for subpkg in sorted(subpackage_names):
            idx.write(f"   {subpkg.replace('_', ' ').capitalize()} <{subpkg}/index>\n")
        # Then write modules
        for modname in sorted(module_names):
            idx.write(f"   {modname.capitalize()} <{modname}>\n")

# Remove .rst files for modules and packages that no longer exist
for root, _dirs, files in os.walk(OUT_BASE, topdown=False):
    rel_root = os.path.relpath(root, OUT_BASE)
    if rel_root.split(os.sep)[0] in SKIP_DIRS:
        continue
    for filename in files:
        path = os.path.normpath(os.path.join(root, filename))
        if filename.endswith(".rst") and path not in written:
            os.remove(path)
            print(f"Removed stale file {os.path.relpath(path, OUT_BASE)}")
    if root != OUT_BASE and not os.listdir(root):
        os.rmdir(root)
