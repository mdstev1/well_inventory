import os
import uuid
import json
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Float, String, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship

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

    # Relationships
    hydrograph = relationship('Hydrograph', back_populates='well', uselist=False)

class Hydrograph(Base):
    """
    SQLAlchemy Hydrograph DB Model
    """
    __tablename__ = 'hydrographs'

    # Columns
    id = Column(Integer, primary_key=True)
    well_id = Column(ForeignKey('wells.id'))

    # Relationships
    well = relationship('Well', back_populates='hydrograph')
    points = relationship('HydrographPoint', back_populates='hydrograph')


class HydrographPoint(Base):
    """
    SQLAlchemy Hydrograph Point DB Model
    """
    __tablename__ = 'hydrograph_points'

    # Columns
    id = Column(Integer, primary_key=True)
    hydrograph_id = Column(ForeignKey('hydrographs.id'))
    time = Column(Integer)  #: hours
    flow = Column(Float)  #: cfs

    # Relationships
    hydrograph = relationship('Hydrograph', back_populates='points')

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

        # Initialize database with two wells
        well1 = Well(
            latitude=40.406624,
            longitude=-111.529133,
            name="Deer Creek",
            owner="Reclamation",
            river="Provo Aquifer",
            date_built="April 12, 1993"
        )

        well2 = Well(
            latitude=40.598168,
            longitude=-111.424055,
            name="Jordanelle",
            owner="Reclamation",
            river="Provo Aquifer",
            date_built="1941"
        )

        # Add the wells to the session, commit, and close
        session.add(well1)
        session.add(well2)
        session.commit()
        session.close()

def assign_hydrograph_to_well(well_id, hydrograph_file):
    """
    Parse hydrograph file and add to database, assigning to appropriate well.
    """
    # Parse file
    hydro_points = []

    try:
        for line in hydrograph_file:
            line = line.decode('utf-8')
            sline = line.split(',')

            try:
                time = int(sline[0])
                flow = float(sline[1])
                hydro_points.append(HydrographPoint(time=time, flow=flow))
            except ValueError:
                continue

        if len(hydro_points) > 0:
            Session = app.get_persistent_store_database('primary_db', as_sessionmaker=True)
            session = Session()

            # Get well object
            well = session.query(Well).get(int(well_id))

            # Overwrite old hydrograph
            hydrograph = well.hydrograph

            # Create new hydrograph if not assigned already
            if not hydrograph:
                hydrograph = Hydrograph()
                well.hydrograph = hydrograph

            # Remove old points if any
            for hydro_point in hydrograph.points:
                session.delete(hydro_point)

            # Assign points to hydrograph
            hydrograph.points = hydro_points

            # Persist to database
            session.commit()
            session.close()

    except Exception as e:
        # Careful not to hide error. At the very least log it to the console
        print(e)
        return False

    return True

def get_hydrograph(well_id):
    """
    Get hydrograph id from well id.
    """
    Session = app.get_persistent_store_database('primary_db', as_sessionmaker=True)
    session = Session()

    # Query if hydrograph exists for well
    hydrograph = session.query(Hydrograph).filter_by(well_id=well_id).first()
    session.close()

    if hydrograph:
        return hydrograph.id
    else:
        return None

