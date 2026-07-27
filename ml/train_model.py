import os
import joblib

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix
)

print("Loading processed data...")

# Load train-test data
X_train, X_test, y_train, y_test = joblib.load(
    "../dataset/CICIDS2017/processed/train_test_data.pkl"
)

print("Training Random Forest Model...")

rf = RandomForestClassifier(
    n_estimators=100,
    random_state=42,
    n_jobs=-1
)

rf.fit(X_train, y_train)

print("\nTraining Completed!")

# -----------------------------
# Prediction
# -----------------------------
print("\nMaking Predictions...")

y_pred = rf.predict(X_test)

# -----------------------------
# Evaluation
# -----------------------------
accuracy = accuracy_score(y_test, y_pred)
precision = precision_score(
    y_test,
    y_pred,
    average="weighted",
    zero_division=0
)
recall = recall_score(
    y_test,
    y_pred,
    average="weighted",
    zero_division=0
)
f1 = f1_score(
    y_test,
    y_pred,
    average="weighted",
    zero_division=0
)

print("\n==============================")
print("MODEL PERFORMANCE")
print("==============================")

print(f"Accuracy : {accuracy:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall   : {recall:.4f}")
print(f"F1 Score : {f1:.4f}")

print("\nClassification Report:\n")

print(
    classification_report(
        y_test,
        y_pred,
        zero_division=0
    )
)

print("\nConfusion Matrix:\n")
print(confusion_matrix(y_test, y_pred))

# -----------------------------
# Save Model
# -----------------------------

SAVE_FOLDER = "saved_models"

# Create folder if it doesn't exist
os.makedirs(SAVE_FOLDER, exist_ok=True)

MODEL_PATH = os.path.join(
    SAVE_FOLDER,
    "random_forest_model.pkl"
)

joblib.dump(rf, MODEL_PATH)

print("\n===================================")
print("Random Forest model saved successfully!")
print(f"Location : {MODEL_PATH}")
print("===================================")