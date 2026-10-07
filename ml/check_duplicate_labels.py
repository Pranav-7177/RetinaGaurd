from pathlib import Path
import hashlib
import pandas as pd
from collections import Counter

BASE = Path("data/raw/aptos2019")
IMAGE_DIR = BASE / "train_images"
CSV_FILE = BASE / "train.csv"

# Load labels
df = pd.read_csv(CSV_FILE)
labels = dict(zip(df["id_code"], df["diagnosis"]))

# Group images by exact file hash
hashes = {}

for image_path in IMAGE_DIR.glob("*.png"):
    file_hash = hashlib.md5(image_path.read_bytes()).hexdigest()

    if file_hash not in hashes:
        hashes[file_hash] = []

    hashes[file_hash].append(image_path.stem)

# Only groups containing duplicates
duplicate_groups = [
    ids for ids in hashes.values()
    if len(ids) > 1
]

same_label_groups = 0
conflicting_groups = 0
conflicting_images = set()
conflicting_transitions = Counter()

for group in duplicate_groups:
    group_labels = [labels[image_id] for image_id in group]

    if len(set(group_labels)) == 1:
        same_label_groups += 1
    else:
        conflicting_groups += 1

        for image_id in group:
            conflicting_images.add(image_id)

        # Record every pair of different labels in this duplicate group
        unique_labels = sorted(set(group_labels))

        for i in range(len(unique_labels)):
            for j in range(i + 1, len(unique_labels)):
                transition = (
                    unique_labels[i],
                    unique_labels[j]
                )
                conflicting_transitions[transition] += 1

print("===================================")
print("   DUPLICATE LABEL ANALYSIS")
print("===================================")

print(f"Total images: {len(list(IMAGE_DIR.glob('*.png')))}")
print(f"Unique image groups: {len(hashes)}")
print(f"Duplicate groups: {len(duplicate_groups)}")

print("\nSame-label duplicate groups:", same_label_groups)
print("Conflicting-label groups:", conflicting_groups)
print("Images involved in conflicts:", len(conflicting_images))

print("\n-----------------------------------")
print("CONFLICTING LABEL TRANSITIONS")
print("-----------------------------------")

if conflicting_transitions:
    for (label_a, label_b), count in sorted(conflicting_transitions.items()):
        print(f"Diagnosis {label_a} ↔ Diagnosis {label_b}: {count} group(s)")
else:
    print("No conflicting labels found.")

print("\n-----------------------------------")
print("DIAGNOSIS MEANING")
print("-----------------------------------")
print("0 = No DR")
print("1 = Mild NPDR")
print("2 = Moderate NPDR")
print("3 = Severe NPDR")
print("4 = Proliferative DR")

print("\nAnalysis complete.")

