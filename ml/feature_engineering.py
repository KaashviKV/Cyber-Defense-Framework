import pandas as pd
import joblib
import os

from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split

# -----------------------------
# Paths
# -----------------------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_DIR = os.path.join(CURRENT_DIR, "saved_models")
os.makedirs(SAVE_DIR, exist_ok=True)

# -----------------------------
# Load Balanced Dataset
# -----------------------------
DATA_PATH = "../dataset/CICIDS2017/processed/balanced_dataset.csv"

print("Loading balanced dataset...")

df = pd.read_csv(DATA_PATH)

print("Dataset Shape:", df.shape)

# -----------------------------
# Remove leading/trailing spaces from column names
# -----------------------------
df.columns = df.columns.str.strip()

# -----------------------------
# Encode Labels
# -----------------------------
print("\nEncoding attack labels...")

label_encoder = LabelEncoder()

df["Label"] = label_encoder.fit_transform(df["Label"])

print("\nClasses Found:")
for i, label in enumerate(label_encoder.classes_):
    print(i, ":", label)

# Save encoder
joblib.dump(label_encoder, os.path.join(SAVE_DIR, "label_encoder.pkl"))

# -----------------------------
# Features and Target
# -----------------------------
X = df.drop("Label", axis=1)
y = df["Label"]

# -----------------------------
# Scale Features
# -----------------------------
print("\nScaling Features...")

scaler = StandardScaler()

X_scaled = scaler.fit_transform(X)

joblib.dump(scaler, os.path.join(SAVE_DIR, "scaler.pkl"))

# -----------------------------
# Train Test Split
# -----------------------------
print("\nSplitting Dataset...")

X_train, X_test, y_train, y_test = train_test_split(
    X_scaled,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

print("\nTraining Samples :", len(X_train))
print("Testing Samples  :", len(X_test))

# -----------------------------
# Save Processed Data
# -----------------------------
joblib.dump(
    (X_train, X_test, y_train, y_test),
    "../dataset/CICIDS2017/processed/train_test_data.pkl",
)

print("\nFeature Engineering Completed Successfully!")
