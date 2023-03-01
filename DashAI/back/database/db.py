from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from DashAI.back.config import settings

engine = create_engine(f"sqlite:///{settings.db_path}")
Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()
