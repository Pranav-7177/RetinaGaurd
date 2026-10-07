from pathlib import Path
import hashlib

IMAGE_DIR = Path("data/raw/aptos2019/train_images")

hashes = {}
duplicates = []

files = list(IMAGE_DIR.glob("*.png"))

print(f"Checking {len(files)} images for exact duplicates...\n")

for i, image_path in enumerate(files, start=1):
    file_hash = hashlib.md5(image_path.read_bytes()).hexdigest()

    if file_hash in hashes:
        duplicates.append((image_path.name, hashes[file_hash]))
    else:
        hashes[file_hash] = image_path.name

    if i % 500 == 0:
        print(f"Checked {i}/{len(files)} images...")

print("\n===================================")
print("       DUPLICATE CHECK")
print("===================================")

print("Total images:", len(files))
print("Unique images:", len(hashes))
print("Duplicate images:", len(duplicates))

if duplicates:
    print("\nDuplicates found:")
    for duplicate, original in duplicates[:20]:
        print(f"{duplicate} == {original}")
else:
    print("\nNo exact duplicate images found! ✅")
    