import os
import uuid
import json
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Float, String
from sqlalchemy.orm import sessionmaker

from .app import WellInventory as app

Base = declarative_base()


# SQLAlchemy ORM definition for the wells table
class Well(Base):
    """
    SQLAlchemy Well DB Model
    """
    __tablename__ = 'wells'

    # Columns
    id = Column(Integer, primary_key=True)
    latitude = Column(Float)
    longitude = Column(Float)
    name = Column(String)
    owner = Column(String)
    river = Column(String)
    date_built = Column(String)


def add_new_well(location, name, owner, river, date_built):
    """
    Persist new well.
    """
    # Convert GeoJSON to Python dictionary
    location_dict = json.loads(location)
    location_geometry = location_dict['geometries'][0]
    longitude = location_geometry['coordinates'][0]
    latitude = location_geometry['coordinates'][1]

    # Create new Well record
    new_well = Well(
        latitude=latitude,
        longitude=longitude,
        name=name,
        owner=owner,
        river=river,
        date_built=date_built
    )

    # Get connection/session to database
    Session = app.get_persistent_store_database('primary_db', as_sessionmaker=True)
    session = Session()

    # Add the new well record to the session
    session.add(new_well)

    # Commit the session and close the connection
    session.commit()
    session.close()


def get_all_wells():
    """
    Get all persisted wells.
    """
    # Get connection/session to database
    Session = app.get_persistent_store_database('primary_db', as_sessionmaker=True)
    session = Session()

    # Query for all well records
    wells = session.query(Well).all()
    session.close()

    return wells


def init_primary_db(engine, first_time):
    """
    Initializer for the primary database.
    """
    # Create all the tables
    Base.metadata.create_all(engine)

    # Add data
    if first_time:
        # Make session
        Session = sessionmaker(bind=engine)
        session = Session()

        # Initialize database with two dams
        well1 = Well(
            latitude=40.406624,
            longitude=-111.529133,
            name="Deer Creek",
            owner="Reclamation",
            river="Provo River",
            date_built="April 12, 1993"
        )

        well2 = Well(
            latitude=40.598168,
            longitude=-111.424055,
            name="Jordanelle",
            owner="Reclamation",
            river="Provo River",
            date_built="1941"
        )

        # Add the wells to the session, commit, and close
        session.add(well1)
        session.add(well2)
        session.commit()
        session.close()

