from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from DashAI.back.containers import Container

engine = create_engine(f"sqlite:///{settings.DB_PATH}")
SessionLocal = sessionmaker(bind=engine)
