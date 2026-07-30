import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite database file path
DATABASE_URL = "sqlite:///./smartcivic.db"

# Create SQLAlchemy engine for SQLite (connect_args check_same_thread False for multi-threading)
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

# SessionLocal factory for DB sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base class for models
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
