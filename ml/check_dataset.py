from pathlib import Path
from PIL import Image
import pandas as pd
from collections import Counter

# APTOS dataset location
BASE = Path("data/raw/aptos2019")
IMAGE_DIR = BASE / "train_images"
CSV_FILE = BASE / "train.csv"

# Read the labels
df = pd.read_csv(CSV_FILE)

bad_images = []
sizes = Counter()
formats = Counter()

# Check every labeled image
for image_id in df["id_code"]:
    image_path = IMAGE_DIR / f"{image_id}.png"

    try:
        # Check if image is valid
        with Image.open(image_path) as img:
            img.verify()

        # Read image information
        with Image.open(image_path) as img:
            sizes[img.size] += 1
            formats[img.format] += 1

    except Exception as e:
        bad_images.append((image_id, str(e)))

# Print results
print("===================================")
print("       APTOS DATASET CHECK")
print("===================================")

print("Total CSV records:", len(df))
print("Bad/corrupted images:", len(bad_images))

print("\nImage formats:")
for fmt, count in formats.items():
    print(f"  {fmt}: {count}")

print("\nMost common image dimensions:")
for size, count in sizes.most_common(10):
    print(f"  {size}: {count}")

if bad_images:
    print("\nProblematic images:")
    for image_id, error in bad_images[:20]:
        print(f"  {image_id} -> {error}")
else:
    print("\nNo corrupted images found! ✅")