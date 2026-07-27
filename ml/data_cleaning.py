import pandas as pd
import os

INPUT_FILE = "../dataset/CICIDS2017/processed/merged_dataset.csv"
OUTPUT_FILE = "../dataset/CICIDS2017/processed/balanced_dataset.csv"

CHUNK_SIZE = 100000
SAMPLE_SIZE = 20000

chunks = []

print("Reading dataset in chunks...\n")

for chunk in pd.read_csv(INPUT_FILE, chunksize=CHUNK_SIZE, low_memory=False):

    print(f"Processing {len(chunk)} rows...")

    # Remove duplicates inside each chunk
    chunk = chunk.drop_duplicates()

    # Replace infinite values
    chunk = chunk.replace([float("inf"), float("-inf")], pd.NA)

    # Remove missing values
    chunk = chunk.dropna()

    # Random sample from this chunk
    if len(chunk) > SAMPLE_SIZE:
        chunk = chunk.sample(n=SAMPLE_SIZE, random_state=42)

    chunks.append(chunk)

print("\nMerging sampled chunks...")

balanced_df = pd.concat(chunks, ignore_index=True)

print("\nFinal Dataset Shape:")
print(balanced_df.shape)

balanced_df.to_csv(OUTPUT_FILE, index=False)

print("\nBalanced dataset saved successfully!")
print(OUTPUT_FILE)
