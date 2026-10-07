from pathlib import Path
import hashlib
import pandas as pd

BASE = Path("data/raw/aptos2019")
IMAGE_DIR = BASE / "train_images"
CSV_FILE = BASE / "train.csv"

OUTPUT_DIR = Path("data/processed")
OUTPUT_FILE = OUTPUT_DIR / "aptos_clean.csv"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load original labels
df = pd.read_csv(CSV_FILE)

# Map image ID -> diagnosis
labels = dict(zip(df["id_code"], df["diagnosis"]))

# Group identical images using MD5 hash
hash_groups = {}

for image_path in IMAGE_DIR.glob("*.png"):
    file_hash = hashlib.md5(image_path.read_bytes()).hexdigest()

    if file_hash not in hash_groups:
        hash_groups[file_hash] = []

    hash_groups[file_hash].append(image_path.stem)

clean_records = []
excluded_conflicts = 0
excluded_duplicate_copies = 0

for group in hash_groups.values():

    group_labels = [labels[image_id] for image_id in group]

    # Conflicting labels → exclude entire group
    if len(set(group_labels)) > 1:
        excluded_conflicts += len(group)
        continue

    # Same label → keep only one copy
    image_id = group[0]
    diagnosis = labels[image_id]

    clean_records.append({
        "id_code": image_id,
        "diagnosis": diagnosis
    })

    excluded_duplicate_copies += len(group) - 1

# Create clean dataframe
clean_df = pd.DataFrame(clean_records)

# Sort for reproducibility
clean_df = clean_df.sort_values("id_code").reset_index(drop=True)

# Save
clean_df.to_csv(OUTPUT_FILE, index=False)

print("===================================")
print("     CLEAN DATASET CREATED")
print("===================================")

print(f"Original images: {len(df)}")
print(f"Clean images: {len(clean_df)}")
print(f"Removed duplicate copies: {excluded_duplicate_copies}")
print(f"Excluded conflicting images: {excluded_conflicts}")

print("\nClean class distribution:")
print(clean_df["diagnosis"].value_counts().sort_index())

print(f"\nSaved to:")
print(OUTPUT_FILE)

print("\n✅ Raw dataset was NOT modified.")

