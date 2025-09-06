from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = "postgresql+psycopg2://drop-cars:Dropcars3456?@34.131.146.2:5432/drop-cars"

engine = create_engine(DATABASE_URL, connect_args={"options": "-c search_path=drop-cars"})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency for DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
