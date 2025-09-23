import logging

from sqlalchemy import Boolean, Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import create_engine
from sqlalchemy import event
from sqlalchemy import text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

Base = declarative_base()

PERIOD_COLUMNS = ["aar"]


def period_columns():
    """Generate Column definitions for period dimensions"""
    return {name: Column(String, primary_key=True) for name in PERIOD_COLUMNS}


class Enheter(Base):
    __tablename__ = "enheter"
    locals().update(period_columns())
    ident = Column(String, primary_key=True)
    skjema = Column(String, primary_key=True)


class Enhetsinfo(Base):
    __tablename__ = "enhetsinfo"
    locals().update(period_columns())
    ident = Column(String, primary_key=True)
    variabel = Column(String, primary_key=True)
    verdi = Column(String)


class Skjemamottak(Base):
    __tablename__ = "skjemamottak"
    locals().update(period_columns())
    ident = Column(String, ForeignKey("enheter.ident"), primary_key=True)
    skjema = Column(String, ForeignKey("enheter.skjema"), primary_key=True)
    refnr = Column(String, primary_key=True)
    dato_mottatt = Column(String)
    editert = Column(Boolean)
    kommentar = Column(String)
    aktiv = Column(Boolean)


class Kontaktinfo(Base):
    __tablename__ = "kontaktinfo"
    locals().update(period_columns())
    ident = Column(String, ForeignKey("enheter.ident"), primary_key=True)
    skjema = Column(String, ForeignKey("enheter.skjema"), primary_key=True)
    refnr = Column(String, ForeignKey("skjemamottak.refnr"), primary_key=True)
    kontaktperson = Column(String, nullable=True)
    epost = Column(String, nullable=True)
    telefon = Column(String, nullable=True)
    bekreftet_kontaktinfo = Column(String, nullable=True)
    kommentar_kontaktinfo = Column(String, nullable=True)
    kommentar_krevende = Column(String, nullable=True)


class Kontroller(Base):
    __tablename__ = "kontroller"
    locals().update(period_columns())
    skjema = Column(String, ForeignKey("enheter.skjema"), primary_key=True)
    kontrollid = Column(String, primary_key=True)
    kontrolltype = Column(String)
    skildring = Column(String)
    kontrollvariabel = Column(String)
    sorteringsvariabel = Column(String)


class Kontrollutslag(Base):
    __tablename__ = "kontrollutslag"
    locals().update(period_columns())
    kontrollid = Column(String, ForeignKey("kontroller.kontrollid"), primary_key=True)
    skjema = Column(String, ForeignKey("enheter.skjema"), primary_key=True)
    ident = Column(String, ForeignKey("enheter.ident"), primary_key=True)
    refnr = Column(String, ForeignKey("skjemamottak.refnr"), primary_key=True)
    utslag = Column(Boolean)
    verdi = Column(Integer)  # Maybe other type?


class Skjemadata_hoved(Base):
    __tablename__ = "skjemadata_hoved"
    locals().update(period_columns())
    skjema = Column(String, ForeignKey("enheter.skjema"), primary_key=True)
    ident = Column(String, ForeignKey("enheter.ident"), primary_key=True)
    refnr = Column(String, ForeignKey("skjemamottak.refnr"), primary_key=True)
    variabel = Column(String, primary_key=True)
    verdi = Column(String)


class Datatyper(Base):
    __tablename__ = "datatyper"
    locals().update(period_columns())
    variabel = Column(String)
    datatype = Column(String)
    tabell = Column(String)
    radnr = Column(String)

def create_engine(database_type):
    if database_type == "sqlite":
        engine = create_engine("sqlite:///mydb.sqlite", echo=True)
    else:
        raise ValueError(f"Unsupported database type: {database_type}")
    return engine


def create_database(engine):
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    engine = create_engine("sqlite")
    create_database(engine)
    conn = engine.connect()
    result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
    print("Existing tables:")
    for row in result:
        print(row)
