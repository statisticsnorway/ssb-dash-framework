from ssb_dash_framework import DemoDataCreator, create_database_engine, create_database

def create_demo_data():
    engine = create_database_engine("sqlite")
    create_database(engine)
    DemoDataCreator(engine).build_demo_database()

create_demo_data()
