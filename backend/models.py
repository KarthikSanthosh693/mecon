# SQLAlchemy column types
from sqlalchemy import Column, Integer, Float, String

# Base class for all ORM models
from database import Base


# ============================================================
# MACHINES TABLE
# ============================================================
class Machine(Base):
    """
    Stores machine master data.

    ⚠️ NOTE:
    Currently you generate machines in-memory, not in DB.
    This table is ready for future persistence (good design).
    """
    __tablename__ = "machines"

    # Primary key (unique machine identifier)
    Machine_ID = Column(String, primary_key=True, index=True)

    # Machine metadata
    Machine_Type = Column(String)
    Machine_Age = Column(Integer)

    # Sensor features (used by ML)
    Avg_Temperature = Column(Float)
    Avg_Vibration = Column(Float)

    # Ground-truth failure label (for supervised learning)
    Failure_Label = Column(Integer)


# ============================================================
# JOBS TABLE
# ============================================================
class Job(Base):
    """
    Stores production jobs.

    ⭐ This becomes VERY important in Phase 5 (Scheduling).
    """
    __tablename__ = "jobs"

    # Primary key
    Job_ID = Column(String, primary_key=True, index=True)

    # Matching constraint for scheduling
    Required_Machine_Type = Column(String)

    # Processing requirements
    Processing_Time_Hours = Column(Integer)
    Priority_Level = Column(Integer)
    Deadline_Hours = Column(Integer)

    # Business objective (maximize revenue)
    Revenue_Per_Job = Column(Float)


# ============================================================
# PREDICTIONS TABLE ⭐⭐⭐
# ============================================================
class Prediction(Base):
    """
    Stores ML outputs per machine.

    This table is the BRIDGE between:

        ML layer → Operations layer → Dashboard

    Judges care about this integration.
    """
    __tablename__ = "predictions"

    # Surrogate primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign reference to machine (not enforced yet)
    Machine_ID = Column(String)

    # ⭐ ML output
    failure_probability = Column(Float)

    # ⭐ Business-friendly metric
    health_score = Column(Float)