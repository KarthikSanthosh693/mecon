# ----------------------------
# Import internal modules
# ----------------------------
from scheduler import optimize_schedule
from simulation import simulate_maintenance  # ⭐ Phase 3 simulation engine
from ml_utils import train_model, load_model, compute_health_score  # ⭐ ML utilities
from database import SessionLocal
from models import Prediction

# Standard libraries
import numpy as np
import random
import pandas as pd
from faker import Faker

# FastAPI & DB setup
from database import engine
from models import Base
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


# ----------------------------
# FastAPI app initialization
# ----------------------------
app = FastAPI(title="MECON AI Platform")

# Create database tables if not exist
Base.metadata.create_all(bind=engine)


# ----------------------------
# CORS (allows frontend to call backend)
# ----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ open for hackathon; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

fake = Faker()

# ----------------------------
# In-memory storage (temporary)
# NOTE: This is fine for hackathon demo
# ----------------------------
machines_data = []
jobs_data = []


# ============================================================
# HEALTH CHECK
# ============================================================
@app.get("/health")
def health():
    """Simple endpoint to verify backend is running"""
    return {"status": "ok"}


# ============================================================
# PHASE 1 — Synthetic Data Generator ⭐
# ============================================================
@app.post("/generate-data")
def generate_data():
    """
    Generates synthetic machines and jobs.
    This simulates real industrial telemetry.
    """

    global machines_data, jobs_data

    # ---------- MACHINE TYPES ----------
    machine_types = ["CNC", "Lathe", "Milling", "Drill"]

    machines = []

    # ⭐ Generate ≥10 machines (MECON requirement)
    for i in range(10):
        age = random.randint(1, 10)
        vibration = round(random.uniform(0.5, 5.0), 2)
        temperature = round(random.uniform(40, 95), 2)

        # ⭐ Correlated failure probability (important for ML learning)
        failure_prob = min(
            1.0,
            (age * 0.05 + vibration * 0.08 + (temperature - 40) * 0.01)
        )

        machines.append({
            "Machine_ID": f"M{i+1}",
            "Machine_Type": random.choice(machine_types),
            "Installation_Year": 2015 + random.randint(0, 8),
            "Machine_Age": age,
            "Total_Run_Hours": random.randint(2000, 20000),
            "Avg_Load_Percentage": random.randint(40, 95),
            "Daily_Operating_Hours": random.randint(8, 24),
            "Capacity_Per_Hour": random.randint(5, 20),
            "Avg_Temperature": temperature,
            "Avg_Vibration": vibration,
            "Energy_Consumption_Rate": round(random.uniform(10, 50), 2),
            "Last_Maintenance_Days": random.randint(1, 180),
            "Failure_History_Count": random.randint(0, 5),
            "Downtime_Hours_Last_Year": random.randint(10, 200),
            "Maintenance_Cost_Last_Year": random.randint(1000, 10000),

            # ⭐ Ground-truth label for supervised learning
            "Failure_Label": 1 if failure_prob > 0.6 else 0
        })

    # ---------- JOBS (≥50 required) ----------
    jobs = []
    for j in range(50):
        jobs.append({
            "Job_ID": f"J{j+1}",
            "Required_Machine_Type": random.choice(machine_types),
            "Processing_Time_Hours": random.randint(1, 10),
            "Load_Requirement_Percentage": random.randint(30, 90),
            "Priority_Level": random.randint(1, 5),
            "Deadline_Hours": random.randint(12, 120),
            "Revenue_Per_Job": random.randint(500, 5000)
        })

    machines_data = machines
    jobs_data = jobs

    return {
        "message": "Synthetic data generated",
        "machines": len(machines_data),
        "jobs": len(jobs_data)
    }


# ============================================================
# DATA ACCESS ENDPOINTS
# ============================================================
@app.get("/machines")
def get_machines():
    """Returns generated machine dataset"""
    return machines_data

# ============================================================
# JOBS
# ============================================================

@app.get("/jobs")
def get_jobs():
    """Returns generated job dataset"""
    return jobs_data


# ============================================================
# PHASE 2 — ML TRAINING PIPELINE ⭐⭐⭐
# ============================================================
@app.post("/train-model")
def train_failure_model():
    """
    Trains Random Forest model and computes:
    - failure probability
    - health score
    Stores results in database.
    """

    global machines_data

    if not machines_data:
        return {"error": "Generate data first"}

    # ⭐ Train ML model
    model, metrics = train_model(machines_data)

    db = SessionLocal()

    # ⭐ Clear previous predictions (important)
    db.query(Prediction).delete(synchronize_session=False)
    db.commit()

    df = pd.DataFrame(machines_data)

    # Features used by the model
    features = [
        "Machine_Age",
        "Avg_Temperature",
        "Avg_Vibration",
        "Failure_History_Count",
        "Downtime_Hours_Last_Year",
    ]

    # ⭐ Predict failure probability
    proba = model.predict_proba(df[features])

    # Handle single-class edge case
    if proba.shape[1] == 1:
        probs = proba[:, 0]
    else:
        probs = proba[:, 1]

    results = []

    # ⭐ Compute health score per machine
    for machine, prob in zip(machines_data, probs):
        health = compute_health_score(
            prob,
            machine["Avg_Vibration"],
            machine["Avg_Temperature"],
        )

        # ⭐ Persist prediction
        pred = Prediction(
            Machine_ID=machine["Machine_ID"],
            failure_probability=float(prob),
            health_score=float(health),
        )

        db.add(pred)

        results.append({
            "Machine_ID": machine["Machine_ID"],
            "failure_probability": float(prob),
            "health_score": float(health),
        })

    db.commit()
    db.close()

    return {
        "message": "Model trained",
        "metrics": metrics,
        "predictions": results[:5],  # sample preview
    }


# ============================================================
# RISK CLASSIFICATION LAYER ⭐
# ============================================================
@app.get("/high-risk-machines")
def get_high_risk_machines():
    """
    Converts numeric health score into business-friendly risk labels.
    This powers the dashboard.
    """

    db = SessionLocal()
    preds = db.query(Prediction).all()

    results = []

    for p in preds:
        # ⭐ Risk banding logic
        if p.health_score >= 80:
            status = "Healthy"
        elif p.health_score >= 50:
            status = "Warning"
        else:
            status = "High Risk"

        results.append({
            "Machine_ID": p.Machine_ID,
            "failure_probability": p.failure_probability,
            "health_score": p.health_score,
            "risk_level": status,
        })

    db.close()
    return results


# ============================================================
# PHASE 3 — Maintenance Simulation ⭐⭐⭐
# ============================================================
@app.get("/simulate-maintenance")
def run_maintenance_simulation():
    """
    Runs preventive vs delayed maintenance comparison.
    Uses ML predictions as input.
    """

    db = SessionLocal()
    preds = db.query(Prediction).all()

    if not preds:
        db.close()
        return {"error": "Run training first"}

    # ⭐ Core simulation engine
    results = simulate_maintenance(preds)

    db.close()
    return results
# ============================================================
# PHASE 5 — Schedule Optimization ⭐⭐⭐
# ============================================================
@app.post("/optimize-schedule")
def optimize_production_schedule(
    w_throughput: float = 0.4,
    w_risk: float = 0.3,
    w_cost: float = 0.3,
):
    """
    Runs multi-objective scheduling.

    Uses:
    - machines (synthetic)
    - jobs (synthetic)
    - ML health predictions

    Returns machine-wise job timeline.
    """

    global machines_data, jobs_data

    db = SessionLocal()
    preds = db.query(Prediction).all()

    if not machines_data or not jobs_data:
        db.close()
        return {"error": "Generate data first"}

    if not preds:
        db.close()
        return {"error": "Run training first"}

    result = optimize_schedule(
        machines_data,
        jobs_data,
        preds,
        w_throughput,
        w_risk,
        w_cost,
    )

    db.close()
    return result