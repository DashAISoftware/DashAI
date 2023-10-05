from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from DashAI.back.core.config import settings

engine = create_engine(f"sqlite:///{settings.DB_PATH}")
SessionLocal = sessionmaker(bind=engine)
