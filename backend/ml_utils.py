# ============================================================
# IMPORTS
# ============================================================

import numpy as np
import pandas as pd

# Random Forest classifier for failure prediction
from sklearn.ensemble import RandomForestClassifier

# For splitting dataset into train/test
from sklearn.model_selection import train_test_split

# Evaluation metrics (required by MECON)
from sklearn.metrics import accuracy_score, f1_score

# For saving/loading trained model
import joblib


# ============================================================
# MODEL SAVE PATH
# ============================================================
# The trained model will be stored in this file.
MODEL_PATH = "rf_model.joblib"


# ============================================================
# FEATURE PREPARATION
# ============================================================
def prepare_features(machines):
    """
    Converts raw machine JSON list into ML-ready format.

    Input:
        machines → list of machine dictionaries

    Output:
        X → feature matrix (inputs to model)
        y → target labels (Failure_Label)
        df → full dataframe (sometimes useful later)
    """

    # Convert list of dicts → pandas dataframe
    df = pd.DataFrame(machines)

    # Selected predictive features
    # These simulate real industrial sensor + history signals
    features = [
        "Machine_Age",
        "Avg_Temperature",
        "Avg_Vibration",
        "Failure_History_Count",
        "Downtime_Hours_Last_Year",
    ]

    # Feature matrix
    X = df[features]

    # Target variable (what we want to predict)
    y = df["Failure_Label"]

    return X, y, df


# ============================================================
# MODEL TRAINING PIPELINE ⭐
# ============================================================
def train_model(machines):
    """
    Trains Random Forest model to predict machine failure.

    Steps:
    1. Prepare features
    2. Train-test split
    3. Train Random Forest
    4. Evaluate model
    5. Save model to disk
    """

    # Step 1 — prepare ML inputs
    X, y, df = prepare_features(machines)

    # Step 2 — split into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,      # 20% for testing
        random_state=42     # ensures reproducibility
    )

    # Step 3 — initialize Random Forest
    model = RandomForestClassifier(
        n_estimators=100,   # number of trees
        random_state=42
    )

    # Train the model
    model.fit(X_train, y_train)

    # Step 4 — evaluate model performance
    preds = model.predict(X_test)

    metrics = {
        "accuracy": float(accuracy_score(y_test, preds)),
        "f1_score": float(f1_score(y_test, preds)),
    }

    # Step 5 — save trained model for reuse
    joblib.dump(model, MODEL_PATH)

    return model, metrics


# ============================================================
# LOAD SAVED MODEL
# ============================================================
def load_model():
    """
    Loads previously trained model from disk.
    Useful for inference without retraining.
    """
    return joblib.load(MODEL_PATH)


# ============================================================
# MACHINE HEALTH SCORE ⭐⭐⭐ (IMPORTANT FOR DASHBOARD)
# ============================================================
def compute_health_score(prob, vibration, temperature):
    """
    Converts raw ML failure probability + sensor stress
    into a human-friendly 0–100 health score.

    Higher score → healthier machine
    Lower score → higher risk
    """

    # --------------------------------------------------------
    # Risk contribution (largest weight)
    # Failure probability contributes up to 60 points of risk
    # --------------------------------------------------------
    risk_component = prob * 60

    # --------------------------------------------------------
    # Vibration stress (scaled to max 20)
    # Assumes vibration ~0–5 range
    # --------------------------------------------------------
    vib_component = min(vibration / 5.0, 1.0) * 20

    # --------------------------------------------------------
    # Temperature stress (scaled to max 20)
    # Baseline assumed at 40°C
    # --------------------------------------------------------
    temp_component = min((temperature - 40) / 60, 1.0) * 20

    # --------------------------------------------------------
    # Final health score (0–100)
    # --------------------------------------------------------
    health = 100 - (risk_component + vib_component + temp_component)

    # Clamp to valid range
    return max(0, min(100, health))