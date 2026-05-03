from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# create_engine sets up the connection pool
engine = create_engine(DATABASE_URL)

# SessionLocal is a factory -- each request gets its own session
SessionLocal = sessionmaker(autocommit = False, autoflush = False, bind = engine)

# Base class all SQLAlchemy models will inherit from
class Base(DeclarativeBase):
    pass

# Dependency -- FastAPI calls this for every request that needs DB access
def get_db():
    db = SessionLocal()
    try:
        yield db        # hand the session to the route
    finally:
        db.close()      # always close, even if the route crashes