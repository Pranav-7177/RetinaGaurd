import argparse
from pathlib import Path
import sys
import time
from typing import Optional

# Ensure unbuffered/line-buffered stdout for real-time logging
if hasattr(sys.stdout, "reconfigure"):
    getattr(sys.stdout, "reconfigure")(line_buffering=True)

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score
import torch
import torch.nn as nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import ReduceLROnPlateau
from torch.utils.data import DataLoader

# Project directory resolution
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ML_DIR = PROJECT_ROOT / "ml"

if str(ML_DIR) not in sys.path:
    sys.path.insert(0, str(ML_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dataset import RetinaDataset
from model import create_model

# Default Configuration & Paths
TRAIN_CSV = PROJECT_ROOT / "data" / "processed" / "train.csv"
VAL_CSV = PROJECT_ROOT / "data" / "processed" / "validation.csv"
IMAGE_DIR = PROJECT_ROOT / "data" / "raw" / "aptos2019" / "train_images"
MODELS_DIR = PROJECT_ROOT / "models"
CHECKPOINT_PATH = MODELS_DIR / "retinaguard_best.pth"
RESUME_CHECKPOINT_PATH = MODELS_DIR / "retinaguard_resume.pth"

BATCH_SIZE = 16
NUM_EPOCHS = 10
LEARNING_RATE = 1e-4
WEIGHT_DECAY = 1e-4
NUM_CLASSES = 5
NUM_WORKERS = 0  # Set to 0 for cross-platform and Windows multiprocessing stability


def get_device() -> torch.device:
    """Detect and select CUDA if available, else CPU. Prints device details."""
    if torch.cuda.is_available():
        device = torch.device("cuda")
        print(f"Selected device: {device}")
        print(f"GPU Name:        {torch.cuda.get_device_name(0)}")
    else:
        device = torch.device("cpu")
        print(f"Selected device: {device}")
    return device


def calculate_class_weights(
    csv_path: Path,
    num_classes: int = NUM_CLASSES,
    strategy: str = "balanced",
    device: Optional[torch.device] = None,
) -> torch.Tensor:
    """
    Calculate class weights from training set labels to handle class imbalance.
    Strategies:
      - 'balanced': standard inverse frequency N / (K * counts)
      - 'conservative': square-root inverse frequency sqrt(N / counts) normalized to sum to K
    """
    df = pd.read_csv(csv_path)
    total_samples = len(df)
    counts = np.bincount(df["diagnosis"].to_numpy(dtype=np.int64), minlength=num_classes).astype(np.float32)

    if strategy == "conservative":
        raw_weights = np.sqrt(total_samples / counts)
        weights = num_classes * (raw_weights / np.sum(raw_weights))
    elif strategy == "balanced":
        weights = total_samples / (num_classes * counts)
    else:
        raise ValueError(f"Unknown weights strategy: {strategy}. Choose 'balanced' or 'conservative'.")

    weights_tensor = torch.tensor(weights, dtype=torch.float32)
    if device is not None:
        weights_tensor = weights_tensor.to(device)
    return weights_tensor


def train_epoch(model, dataloader, criterion, optimizer, device):
    """Run one epoch of training and return loss, accuracy, and macro F1."""
    model.train()
    running_loss = 0.0
    all_targets = []
    all_predictions = []

    for images, targets in dataloader:
        images = images.to(device)
        targets = targets.to(device)

        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, targets)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * images.size(0)
        _, preds = torch.max(outputs, 1)

        all_targets.extend(targets.cpu().numpy())
        all_predictions.extend(preds.cpu().numpy())

    epoch_loss = running_loss / len(dataloader.dataset)
    epoch_acc = accuracy_score(all_targets, all_predictions)
    epoch_f1 = f1_score(all_targets, all_predictions, average="macro")

    return epoch_loss, epoch_acc, epoch_f1


def validate_epoch(model, dataloader, criterion, device):
    """Run one epoch of validation and return loss, accuracy, and macro F1."""
    model.eval()
    running_loss = 0.0
    all_targets = []
    all_predictions = []

    with torch.no_grad():
        for images, targets in dataloader:
            images = images.to(device)
            targets = targets.to(device)

            outputs = model(images)
            loss = criterion(outputs, targets)

            running_loss += loss.item() * images.size(0)
            _, preds = torch.max(outputs, 1)

            all_targets.extend(targets.cpu().numpy())
            all_predictions.extend(preds.cpu().numpy())

    epoch_loss = running_loss / len(dataloader.dataset)
    epoch_acc = accuracy_score(all_targets, all_predictions)
    epoch_f1 = f1_score(all_targets, all_predictions, average="macro")

    return epoch_loss, epoch_acc, epoch_f1


def train(
    train_csv: Path = TRAIN_CSV,
    val_csv: Path = VAL_CSV,
    image_dir: Path = IMAGE_DIR,
    models_dir: Path = MODELS_DIR,
    checkpoint_path: Path = CHECKPOINT_PATH,
    resume_checkpoint_path: Path = RESUME_CHECKPOINT_PATH,
    batch_size: int = BATCH_SIZE,
    epochs: int = NUM_EPOCHS,
    stop_epoch: Optional[int] = None,
    resume_path: Optional[str | Path] = None,
    lr: float = LEARNING_RATE,
    weight_decay: float = WEIGHT_DECAY,
    num_classes: int = NUM_CLASSES,
    num_workers: int = NUM_WORKERS,
    weights_strategy: str = "balanced",
):
    """Full training pipeline for RetinaGuard model with transfer learning and resume support."""
    session_start_time = time.time()
    print("==================================================================")
    print("                 RETINAGUARD TRAINING PIPELINE")
    print("==================================================================")

    # Ensure models directory exists
    models_dir.mkdir(parents=True, exist_ok=True)

    # Device detection
    device = get_device()

    # Load datasets
    print(f"\nLoading training data from:   {train_csv}")
    print(f"Loading validation data from: {val_csv}")
    print(f"Loading images from:          {image_dir}")

    train_dataset = RetinaDataset(
        csv_file=train_csv,
        image_dir=image_dir,
        training=True,
    )
    val_dataset = RetinaDataset(
        csv_file=val_csv,
        image_dir=image_dir,
        training=False,
    )

    print(f"Training samples:   {len(train_dataset)}")
    print(f"Validation samples: {len(val_dataset)}")

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=(device.type == "cuda"),
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=(device.type == "cuda"),
    )

    # Compute class weights for imbalanced classes
    class_weights = calculate_class_weights(
        train_csv, num_classes=num_classes, strategy=weights_strategy, device=device
    )
    print(f"\nCalculated Class Weights ({weights_strategy}):")
    for cls_idx, weight_val in enumerate(class_weights.cpu().numpy()):
        print(f"  Class {cls_idx}: {weight_val:.4f}")

    criterion = nn.CrossEntropyLoss(weight=class_weights)

    # Instantiate EfficientNet-B0 model
    print("\nInitializing EfficientNet-B0 model...")
    model = create_model(num_classes=num_classes)
    model = model.to(device)

    # Optimizer & ReduceLROnPlateau scheduler based on validation macro F1
    optimizer = AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    scheduler = ReduceLROnPlateau(optimizer, mode="max", factor=0.5, patience=2)

    start_epoch = 1
    best_val_f1 = -1.0
    best_epoch = 0

    # Resume from checkpoint if provided
    if resume_path is not None:
        resume_file = Path(resume_path)
        if not resume_file.exists():
            raise FileNotFoundError(f"Resume checkpoint file not found: {resume_file}")
        print(f"\nLoading resume checkpoint from: {resume_file}")
        ckpt = torch.load(resume_file, map_location=device)

        model.load_state_dict(ckpt["model_state_dict"])
        optimizer.load_state_dict(ckpt["optimizer_state_dict"])
        if "scheduler_state_dict" in ckpt and ckpt["scheduler_state_dict"] is not None:
            scheduler.load_state_dict(ckpt["scheduler_state_dict"])

        completed_epoch = ckpt["epoch"]
        start_epoch = completed_epoch + 1
        best_val_f1 = ckpt.get("best_val_f1", -1.0)
        best_epoch = ckpt.get("best_epoch", completed_epoch if best_val_f1 > -1.0 else 0)
        print(f"[OK] Successfully resumed from epoch {completed_epoch}.")
        print(f"     Next epoch to train: {start_epoch}")
        print(f"     Best Val Macro F1 so far: {best_val_f1:.4f} (Epoch {best_epoch})")

    target_stop = min(stop_epoch, epochs) if stop_epoch is not None else epochs

    print(f"\nHyperparameters:")
    print(f"  Total Target Epochs:  {epochs}")
    print(f"  Session Start Epoch:  {start_epoch}")
    print(f"  Session Target Stop:  {target_stop}")
    print(f"  Batch Size:           {batch_size}")
    print(f"  Learning Rate:        {lr}")
    print(f"  Weight Decay:         {weight_decay}")
    print(f"  Classes:              {num_classes}")
    print(f"  Weights Strategy:     {weights_strategy}")

    if start_epoch > target_stop:
        print(f"\n[OK] Current start epoch ({start_epoch}) is already past target stop ({target_stop}). Nothing to train.")
        return

    print(f"\nStarting training: Epoch {start_epoch} -> Epoch {target_stop} (Total Target: {epochs})...")
    print("-" * 66)

    for epoch in range(start_epoch, target_stop + 1):
        epoch_start = time.time()
        train_loss, train_acc, train_f1 = train_epoch(
            model, train_loader, criterion, optimizer, device
        )
        val_loss, val_acc, val_f1 = validate_epoch(
            model, val_loader, criterion, device
        )

        scheduler.step(val_f1)
        current_lr = optimizer.param_groups[0]["lr"]
        epoch_time = time.time() - epoch_start

        print(
            f"Epoch [{epoch:02d}/{epochs:02d}] (LR: {current_lr:.2e}, Time: {epoch_time:.1f}s)\n"
            f"  Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.4f} | Train Macro F1: {train_f1:.4f}\n"
            f"  Val   Loss: {val_loss:.4f} | Val   Acc: {val_acc:.4f} | Val   Macro F1: {val_f1:.4f}"
        )

        # Track and save best checkpoint based on validation macro F1
        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            best_epoch = epoch
            best_checkpoint = {
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "num_classes": num_classes,
                "best_val_f1": best_val_f1,
            }
            torch.save(best_checkpoint, checkpoint_path)
            print(f"  [BEST] Saved new best checkpoint to {checkpoint_path} (Val Macro F1: {best_val_f1:.4f})")

        # Save resume checkpoint after every completed epoch
        resume_checkpoint = {
            "epoch": epoch,
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "scheduler_state_dict": scheduler.state_dict(),
            "best_val_f1": best_val_f1,
            "best_epoch": best_epoch,
            "num_classes": num_classes,
        }
        torch.save(resume_checkpoint, resume_checkpoint_path)
        print(f"  [OK] Saved resume checkpoint to {resume_checkpoint_path} (Completed Epoch: {epoch})")

        print("-" * 66)

    total_time = time.time() - session_start_time
    print("\n==================================================================")
    if target_stop < epochs:
        print(f"[OK] SESSION COMPLETE: Reached target stop epoch {target_stop}/{epochs}.")
    else:
        print("[OK] TRAINING COMPLETE: All epochs finished.")
    print(f"Session Duration:                 {total_time:.1f}s ({total_time / 60:.2f} min)")
    print(f"Best Validation Macro F1 so far:  {best_val_f1:.4f} (from Epoch {best_epoch})")
    print(f"Best Model Checkpoint:            {checkpoint_path}")
    print(f"Resume Checkpoint:                {resume_checkpoint_path}")
    if target_stop < epochs:
        print(f"Next session instruction: run with --resume (starts at Epoch {target_stop + 1})")
    print("==================================================================")


def main():
    parser = argparse.ArgumentParser(description="RetinaGuard Training Pipeline")
    parser.add_argument(
        "--epochs",
        type=int,
        default=NUM_EPOCHS,
        help=f"Total training target epochs (default: {NUM_EPOCHS})",
    )
    parser.add_argument(
        "--stop-epoch",
        type=int,
        default=None,
        help="Stop training after completing this epoch (e.g., --stop-epoch 5)",
    )
    parser.add_argument(
        "--resume",
        type=str,
        nargs="?",
        const=str(RESUME_CHECKPOINT_PATH),
        default=None,
        help="Path to resume checkpoint file (defaults to models/retinaguard_resume.pth if flag is passed without path)",
    )
    parser.add_argument(
        "--weights-strategy",
        type=str,
        default="balanced",
        choices=["balanced", "conservative"],
        help="Class weighting strategy: 'balanced' or 'conservative' (square-root smoothed) (default: balanced)",
    )
    parser.add_argument(
        "--checkpoint-path",
        type=str,
        default=str(CHECKPOINT_PATH),
        help=f"Path to save best checkpoint (default: {CHECKPOINT_PATH})",
    )
    parser.add_argument(
        "--resume-checkpoint-path",
        type=str,
        default=str(RESUME_CHECKPOINT_PATH),
        help=f"Path to save resume checkpoint (default: {RESUME_CHECKPOINT_PATH})",
    )
    args = parser.parse_args()

    train(
        epochs=args.epochs,
        stop_epoch=args.stop_epoch,
        resume_path=args.resume,
        checkpoint_path=Path(args.checkpoint_path),
        resume_checkpoint_path=Path(args.resume_checkpoint_path),
        weights_strategy=args.weights_strategy,
    )


if __name__ == "__main__":
    main()
