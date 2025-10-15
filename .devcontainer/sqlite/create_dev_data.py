from ssb_dash_framework import DemoDataCreator
from ssb_dash_framework import create_database_engine

DemoDataCreator(
    create_database_engine("sqlite", sqlite_path=".devcontainer/sqlite/mydb.sqlite")
).build_demo_database()
