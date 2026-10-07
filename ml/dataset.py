from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset
from torchvision import transforms


class RetinaDataset(Dataset):
    def __init__(
        self,
        csv_file,
        image_dir,
        training=False,
        image_size=224,
    ):
        self.data = pd.read_csv(csv_file)
        self.image_dir = Path(image_dir)
        self.training = training
        self.image_size = image_size

        if training:
            self.transform = transforms.Compose([
                transforms.ToPILImage(),
                transforms.Resize((image_size, image_size)),
                transforms.RandomHorizontalFlip(p=0.5),
                transforms.RandomRotation(degrees=10),
                transforms.ColorJitter(
                    brightness=0.15,
                    contrast=0.15,
                    saturation=0.1,
                ),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225],
                ),
            ])
        else:
            self.transform = transforms.Compose([
                transforms.ToPILImage(),
                transforms.Resize((image_size, image_size)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225],
                ),
            ])

    def __len__(self):
        return len(self.data)

    def __getitem__(self, index):
        row = self.data.iloc[index]

        image_id = row["id_code"]
        label = int(row["diagnosis"])

        image_path = self.image_dir / f"{image_id}.png"

        image = cv2.imread(str(image_path))

        if image is None:
            raise FileNotFoundError(
                f"Could not load image: {image_path}"
            )

        # OpenCV loads BGR; convert to RGB
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        image = self.transform(image)

        return image, torch.tensor(label, dtype=torch.long)

        