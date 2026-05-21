from unittest.mock import Base

from requests import Session

from app.config import Config
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class DashboardData(Base):
    __tablename__ = 'dashboard_data'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    value = Column(String)
    
engine = create_engine(Config.DATABASE_URI)
SessionLocal = sessionmaker(bind=engine)

class DashboardRepository:
    def get_dashboard_data(self):
        # Create a new database session
        session = session()
        try:
            # Query the dashboard data from the database
            data = session.query(DashboardData).all()
            return data
        finally:
            session.close()