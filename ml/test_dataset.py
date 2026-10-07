from pathlib import Path

from dataset import RetinaDataset


BASE = Path("data/processed")
IMAGE_DIR = Path("data/raw/aptos2019/train_images")


print("===================================")
print("       TESTING DATASET LOADER")
print("===================================")

train_dataset = RetinaDataset(
    csv_file=BASE / "train.csv",
    image_dir=IMAGE_DIR,
    training=True,
)

val_dataset = RetinaDataset(
    csv_file=BASE / "validation.csv",
    image_dir=IMAGE_DIR,
    training=False,
)

test_dataset = RetinaDataset(
    csv_file=BASE / "test.csv",
    image_dir=IMAGE_DIR,
    training=False,
)

print(f"Train samples:      {len(train_dataset)}")
print(f"Validation samples: {len(val_dataset)}")
print(f"Test samples:       {len(test_dataset)}")

# Test one training sample
image, label = train_dataset[0]

print("\nSample check:")
print(f"Image shape: {image.shape}")
print(f"Label: {label.item()}")
print(f"Image dtype: {image.dtype}")

print("\n===================================")

if image.shape == (3, 224, 224):
    print("✅ Image preprocessing works!")
else:
    print("❌ Unexpected image shape.")

if 0 <= label.item() <= 4:
    print("✅ Label is valid!")
else:
    print("❌ Invalid label.")

print("===================================")

