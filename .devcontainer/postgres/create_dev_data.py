from ssb_dash_framework import DemoDataCreator
from ssb_dash_framework import create_database_engine

DemoDataCreator(create_database_engine("postgres")).build_demo_database()
