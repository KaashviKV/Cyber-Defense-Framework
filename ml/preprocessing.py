import pandas as pd
import os
import glob

# Dataset folder
DATASET_PATH = "../dataset/CICIDS2017/raw"

# Get all CSV files
csv_files = glob.glob(os.path.join(DATASET_PATH, "*.csv"))

print(f"Found {len(csv_files)} CSV files.\n")

# List to store DataFrames
dataframes = []

# Read each CSV file
for file in csv_files:
    print(f"Reading: {os.path.basename(file)}")

    df = pd.read_csv(file, low_memory=False)

    print(f"Shape: {df.shape}")

    dataframes.append(df)

# Merge all datasets
merged_df = pd.concat(dataframes, ignore_index=True)

print("\n===================================")
print("Merged Dataset Information")
print("===================================")

print(f"Rows    : {merged_df.shape[0]}")
print(f"Columns : {merged_df.shape[1]}")

print("\nColumn Names:\n")
print(merged_df.columns.tolist())

print("\nAttack Labels:\n")
print(merged_df[' Label'].value_counts())

# Save merged dataset
OUTPUT_PATH = "../dataset/CICIDS2017/processed/merged_dataset.csv"

merged_df.to_csv(OUTPUT_PATH, index=False)

print(f"\nMerged dataset saved to:\n{OUTPUT_PATH}")