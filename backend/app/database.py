from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from core.config import settings

engine = create_engine(settings.DATABASE_URI, echo=False, echo_pool=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Dependency for getting the session in your API endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
