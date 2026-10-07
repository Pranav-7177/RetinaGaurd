from pathlib import Path
import pandas as pd
from sklearn.model_selection import train_test_split

INPUT_FILE = Path("data/processed/aptos_clean.csv")
OUTPUT_DIR = Path("data/processed")

RANDOM_STATE = 42

# Load clean dataset
df = pd.read_csv(INPUT_FILE)

print("===================================")
print("       CREATING DATASET SPLIT")
print("===================================")

print(f"Total clean images: {len(df)}")

# First split: 70% train, 30% temporary
train_df, temp_df = train_test_split(
    df,
    test_size=0.30,
    stratify=df["diagnosis"],
    random_state=RANDOM_STATE
)

# Second split: 15% validation, 15% test
val_df, test_df = train_test_split(
    temp_df,
    test_size=0.50,
    stratify=temp_df["diagnosis"],
    random_state=RANDOM_STATE
)

# Save splits
train_df.to_csv(OUTPUT_DIR / "train.csv", index=False)
val_df.to_csv(OUTPUT_DIR / "validation.csv", index=False)
test_df.to_csv(OUTPUT_DIR / "test.csv", index=False)

print("\nSplit sizes:")
print(f"Train:      {len(train_df)}")
print(f"Validation: {len(val_df)}")
print(f"Test:       {len(test_df)}")

print("\nClass distribution:")
print("\nTRAIN")
print(train_df["diagnosis"].value_counts().sort_index())

print("\nVALIDATION")
print(val_df["diagnosis"].value_counts().sort_index())

print("\nTEST")
print(test_df["diagnosis"].value_counts().sort_index())

print("\n===================================")
print("✅ SPLIT COMPLETE")
print("===================================")

print("\nFiles created:")
print("data/processed/train.csv")
print("data/processed/validation.csv")
print("data/processed/test.csv")
