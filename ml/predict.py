"""
Random Forest Prediction Module

Loads the trained model and predicts
network attack type with confidence.
"""

import os
import joblib
import numpy as np

# ----------------------------------
# Paths
# ----------------------------------

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(
    CURRENT_DIR,
    "saved_models",
    "random_forest_model.pkl"
)

# ----------------------------------
# Load Model
# ----------------------------------

print("Loading Random Forest Model...")

rf_model = joblib.load(MODEL_PATH)

print("Model Loaded Successfully!")

# ----------------------------------
# Attack Severity Mapping
# ----------------------------------

ATTACK_SEVERITY = {

    "BENIGN": 0,
    "Bot": 55,
    "PortScan": 60,
    "FTP-Patator": 65,
    "SSH-Patator": 70,
    "Web Attack – Brute Force": 75,
    "Web Attack – XSS": 85,
    "DoS Hulk": 85,
    "DoS GoldenEye": 82,
    "DoS Slowhttptest": 80,
    "DoS slowloris": 80,
    "Web Attack – Sql Injection": 95,
    "DDoS": 95,
    "Infiltration": 98,
    "Heartbleed": 100
}

# ----------------------------------
# Label Mapping
# ----------------------------------

LABELS = {

    0: "BENIGN",
    1: "Bot",
    2: "DDoS",
    3: "DoS GoldenEye",
    4: "DoS Hulk",
    5: "DoS Slowhttptest",
    6: "DoS slowloris",
    7: "FTP-Patator",
    8: "Heartbleed",
    9: "Infiltration",
    10: "PortScan",
    11: "SSH-Patator",
    12: "Web Attack – Brute Force",
    13: "Web Attack – Sql Injection",
    14: "Web Attack – XSS"
}

# ----------------------------------
# Prediction Function
# ----------------------------------

def predict_attack(features):

    features = np.array(features, dtype=float).reshape(1, -1)

    if features.shape[1] != 78:
        raise ValueError(
            f"Expected 78 features, received {features.shape[1]}."
        )

    prediction = rf_model.predict(features)[0]
    probability = rf_model.predict_proba(features)[0]
    confidence = float(round(max(probability) * 100, 2))

    attack = LABELS.get(int(prediction))
    if attack is None:
        raise ValueError(f"Unknown attack label index: {prediction}")

    severity = ATTACK_SEVERITY.get(attack, 50)

    return {
        "attack": attack,
        "severity": severity,
        "confidence": confidence
    }

# ----------------------------------
# Testing
# ----------------------------------

if __name__ == "__main__":

    print("\nRandom Forest Prediction Test\n")

    dummy = np.random.rand(78)
    result = predict_attack(dummy)
    print(result)
