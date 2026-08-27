"""
Random Forest Prediction Module

Loads the trained model and predicts
network attack type with confidence.
"""

import os
import joblib
import numpy as np

from ml.feature_names import FEATURE_NAMES

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

    from ml.calibration import enrich_confidence

    prediction = rf_model.predict(features)[0]
    probability = rf_model.predict_proba(features)[0]
    calibration = enrich_confidence(features, probability)
    confidence = float(calibration.get("calibrated_confidence") or round(max(probability) * 100, 2))

    attack = LABELS.get(int(prediction))
    if attack is None:
        raise ValueError(f"Unknown attack label index: {prediction}")

    severity = ATTACK_SEVERITY.get(attack, 50)

    return {
        "attack": attack,
        "severity": severity,
        "confidence": confidence,
        "calibration": calibration,
        "class_probabilities": {
            LABELS.get(i, str(i)): round(float(probability[i]) * 100, 2)
            for i in range(len(probability))
            if i in LABELS
        },
    }


def explain_prediction(features, top_n: int = 5) -> dict:
    """
    Local leave-one-feature-out attribution for the predicted class.

    Importance is the drop in predicted-class probability when a feature is
    zeroed. This is a lightweight XAI signal for analysts, not SHAP values.
    """
    features = np.array(features, dtype=float).reshape(1, -1)
    if features.shape[1] != 78:
        raise ValueError(f"Expected 78 features, received {features.shape[1]}.")

    base_proba = rf_model.predict_proba(features)[0]
    pred_idx = int(np.argmax(base_proba))
    attack = LABELS.get(pred_idx, "Unknown")
    names = FEATURE_NAMES[: features.shape[1]]
    if len(names) < features.shape[1]:
        names = [f"Feature {i + 1}" for i in range(features.shape[1])]

    drops = []
    for index in range(features.shape[1]):
        mutated = features.copy()
        mutated[0, index] = 0.0
        new_p = float(rf_model.predict_proba(mutated)[0][pred_idx])
        drop = float(base_proba[pred_idx]) - new_p
        drops.append((names[index], drop))

    ranked = sorted(drops, key=lambda item: item[1], reverse=True)[:top_n]
    return {
        "method": "leave_one_feature_out",
        "predicted_class": attack,
        "predicted_probability": round(float(base_proba[pred_idx]) * 100, 2),
        "caveat": (
            "Shows which input features most support this specific prediction. "
            "Global Random Forest importances remain available separately."
        ),
        "top_features": [
            {"feature": name, "importance": round(max(0.0, float(drop)) * 100, 2)}
            for name, drop in ranked
            if drop > 0
        ] or [
            {"feature": name, "importance": round(abs(float(drop)) * 100, 2)}
            for name, drop in ranked
        ],
    }

# ----------------------------------
# Testing
# ----------------------------------

if __name__ == "__main__":

    print("\nRandom Forest Prediction Test\n")

    dummy = np.random.rand(78)
    result = predict_attack(dummy)
    print(result)
