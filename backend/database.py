# SQLAlchemy core components
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


# ---------------------------------------------------
# Database connection string
# ---------------------------------------------------
# Using SQLite local file database.
# File will be created automatically if it doesn't exist.
DATABASE_URL = "sqlite:///./mecon.db"


# ---------------------------------------------------
# Engine = core connection to the database
# ---------------------------------------------------
engine = create_engine(
    DATABASE_URL,

    # ⭐ REQUIRED for SQLite with FastAPI
    # Allows multiple threads to access the DB
    connect_args={"check_same_thread": False},

    # ⭐ Helps avoid stale connections
    # Good practice for hackathon stability
    pool_pre_ping=True
)


# ---------------------------------------------------
# Session factory
# ---------------------------------------------------
# SessionLocal() is what you use inside endpoints:
#
#   db = SessionLocal()
#
# Think of session as:
# → a conversation with the database
SessionLocal = sessionmaker(bind=engine)


# ---------------------------------------------------
# Base class for ORM models
# ---------------------------------------------------
# All your SQLAlchemy models inherit from this.
#
# Example in models.py:
#   class Prediction(Base):
#       __tablename__ = "predictions"
#
Base = declarative_base()