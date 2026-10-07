from pathlib import Path
import sys

# Ensure unbuffered/line-buffered stdout for real-time logging
if hasattr(sys.stdout, "reconfigure"):
    getattr(sys.stdout, "reconfigure")(line_buffering=True)

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
)
import torch
import torch.nn.functional as F
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

# Constants & Paths
TEST_CSV = PROJECT_ROOT / "data" / "processed" / "test.csv"
IMAGE_DIR = PROJECT_ROOT / "data" / "raw" / "aptos2019" / "train_images"
MODELS_DIR = PROJECT_ROOT / "models"
CHECKPOINT_PATH = MODELS_DIR / "retinaguard_best.pth"
DOCS_DIR = PROJECT_ROOT / "docs"

CONFUSION_MATRIX_PATH = DOCS_DIR / "test_confusion_matrix.png"
EVALUATION_REPORT_PATH = DOCS_DIR / "test_evaluation.txt"
PREDICTIONS_CSV_PATH = DOCS_DIR / "test_predictions.csv"

BATCH_SIZE = 16

CLASS_NAMES = [
    "No DR",
    "Mild NPDR",
    "Moderate NPDR",
    "Severe NPDR",
    "Proliferative DR",
]
NUM_CLASSES = len(CLASS_NAMES)


def get_device() -> torch.device:
    """Detect and select CUDA if available, else CPU."""
    if torch.cuda.is_available():
        device = torch.device("cuda")
        print(f"Selected device: {device} ({torch.cuda.get_device_name(0)})")
    else:
        device = torch.device("cpu")
        print(f"Selected device: {device}")
    return device


def evaluate():
    print("==================================================================")
    print("               RETINAGUARD TEST SET EVALUATION")
    print("==================================================================")

    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Verify files exist
    if not TEST_CSV.exists():
        raise FileNotFoundError(f"Test CSV not found: {TEST_CSV}")
    if not CHECKPOINT_PATH.exists():
        raise FileNotFoundError(f"Best checkpoint not found: {CHECKPOINT_PATH}")
    if not IMAGE_DIR.exists():
        raise FileNotFoundError(f"Image directory not found: {IMAGE_DIR}")

    device = get_device()

    # 2. Load Checkpoint
    print(f"\nLoading best checkpoint from: {CHECKPOINT_PATH}")
    checkpoint = torch.load(CHECKPOINT_PATH, map_location=device)
    best_epoch = checkpoint.get("epoch", "Unknown")
    best_val_f1 = float(checkpoint.get("best_val_f1", 0.0))
    num_classes = int(checkpoint.get("num_classes", NUM_CLASSES))

    print(f"Checkpoint Epoch:             {best_epoch}")
    print(f"Best Validation Macro F1:     {best_val_f1:.4f}")
    print(f"Configured Classes:           {num_classes}")

    # 3. Initialize Model Architecture & Load Weights
    print("\nInitializing EfficientNet-B0 model architecture...")
    model = create_model(num_classes=num_classes)
    model.load_state_dict(checkpoint["model_state_dict"])
    model = model.to(device)
    model.eval()
    print("[OK] Model weights successfully loaded and set to evaluation mode (model.eval()).")

    # 4. Load Test Dataset (NO training augmentation)
    print(f"\nLoading test data from: {TEST_CSV}")
    test_df = pd.read_csv(TEST_CSV)
    num_test_samples = len(test_df)
    print(f"Number of test samples: {num_test_samples}")

    test_dataset = RetinaDataset(
        csv_file=TEST_CSV,
        image_dir=IMAGE_DIR,
        training=False,  # Strict validation/test preprocessing only
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=0,
        pin_memory=(device.type == "cuda"),
    )

    # 5. Run Inference
    print("\nRunning inference on all test images...")
    all_targets: list[int] = []
    all_preds: list[int] = []
    all_probs: list[list[float]] = []

    with torch.no_grad():
        for batch_idx, (images, targets) in enumerate(test_loader):
            images = images.to(device)
            outputs = model(images)
            probs = F.softmax(outputs, dim=1)
            _, preds = torch.max(probs, dim=1)

            all_targets.extend([int(t) for t in targets.cpu().numpy()])
            all_preds.extend([int(p) for p in preds.cpu().numpy()])
            all_probs.extend([[float(v) for v in row] for row in probs.cpu().numpy()])

            if (batch_idx + 1) % 5 == 0 or (batch_idx + 1) == len(test_loader):
                processed = min((batch_idx + 1) * BATCH_SIZE, num_test_samples)
                print(f"  Processed {processed}/{num_test_samples} images...")

    targets_arr = np.array(all_targets, dtype=int)
    preds_arr = np.array(all_preds, dtype=int)

    # 6. Calculate Metrics
    accuracy = float(accuracy_score(targets_arr, preds_arr))
    macro_f1 = float(f1_score(targets_arr, preds_arr, average="macro"))
    weighted_f1 = float(f1_score(targets_arr, preds_arr, average="weighted"))
    correct_predictions = int(np.sum(targets_arr == preds_arr))
    incorrect_predictions = int(num_test_samples - correct_predictions)

    prf_res = precision_recall_fscore_support(
        targets_arr, preds_arr, labels=list(range(NUM_CLASSES))
    )
    precision_per_class = np.asarray(prf_res[0], dtype=float)
    recall_per_class = np.asarray(prf_res[1], dtype=float)
    f1_per_class = np.asarray(prf_res[2], dtype=float)
    support_per_class = np.asarray(prf_res[3], dtype=int) if prf_res[3] is not None else np.zeros(NUM_CLASSES, dtype=int)

    cm = confusion_matrix(targets_arr, preds_arr, labels=list(range(NUM_CLASSES)))

    # 7. Generate and Save Predictions CSV
    predictions_records = []
    for idx in range(num_test_samples):
        img_id = str(test_df.iloc[idx]["id_code"])
        true_cls = int(all_targets[idx])
        pred_cls = int(all_preds[idx])
        pred_name = CLASS_NAMES[pred_cls]
        probs_row = all_probs[idx]
        conf = float(probs_row[pred_cls])

        record = {
            "image_id": img_id,
            "true_class": true_cls,
            "true_class_name": CLASS_NAMES[true_cls],
            "predicted_class": pred_cls,
            "predicted_class_name": pred_name,
            "confidence": round(conf, 6),
            "prob_0": round(float(probs_row[0]), 6),
            "prob_1": round(float(probs_row[1]), 6),
            "prob_2": round(float(probs_row[2]), 6),
            "prob_3": round(float(probs_row[3]), 6),
            "prob_4": round(float(probs_row[4]), 6),
        }
        predictions_records.append(record)

    pred_df = pd.DataFrame(predictions_records)
    pred_df.to_csv(PREDICTIONS_CSV_PATH, index=False)
    print(f"\n[OK] Saved predictions CSV to: {PREDICTIONS_CSV_PATH}")

    # 8. Generate and Save Confusion Matrix Plot
    plt.figure(figsize=(8.5, 7))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=CLASS_NAMES,
        yticklabels=CLASS_NAMES,
        cbar=True,
        annot_kws={"size": 11, "weight": "bold"},
    )
    plt.title("RetinaGuard - Final Test Confusion Matrix (Epoch 6 Best Checkpoint)", fontsize=12, pad=15)
    plt.xlabel("Predicted Class", fontsize=11, labelpad=10)
    plt.ylabel("True Class", fontsize=11, labelpad=10)
    plt.xticks(rotation=30, ha="right")
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(CONFUSION_MATRIX_PATH, dpi=300)
    plt.close()
    print(f"[OK] Saved confusion matrix plot to: {CONFUSION_MATRIX_PATH}")

    # 9. Generate and Save Evaluation Report
    report_lines = [
        "==================================================================",
        "             RETINAGUARD FINAL TEST EVALUATION REPORT",
        "==================================================================",
        "",
        "MODEL INFORMATION:",
        "------------------",
        "Model Architecture:       EfficientNet-B0 (Transfer Learning)",
        f"Checkpoint Used:          {CHECKPOINT_PATH}",
        f"Best Checkpoint Epoch:    {best_epoch}",
        f"Number of Test Samples:   {num_test_samples}",
        f"Best Validation Macro F1: {best_val_f1:.4f}",
        "",
        "OVERALL TEST METRICS:",
        "---------------------",
        f"Test Accuracy:            {accuracy:.4f} ({accuracy * 100:.2f}%)",
        f"Test Macro F1:            {macro_f1:.4f}",
        f"Test Weighted F1:         {weighted_f1:.4f}",
        f"Correct Predictions:      {correct_predictions} / {num_test_samples}",
        f"Incorrect Predictions:    {incorrect_predictions} / {num_test_samples}",
        "",
        "PER-CLASS METRICS:",
        "------------------",
        f"{'Class ID':<10} {'Class Name':<20} {'Samples':<10} {'Precision':<12} {'Recall':<12} {'F1-Score':<10}",
        "-" * 74,
    ]

    for cls_idx in range(NUM_CLASSES):
        report_lines.append(
            f"{cls_idx:<10} {CLASS_NAMES[cls_idx]:<20} {int(support_per_class[cls_idx]):<10} "
            f"{float(precision_per_class[cls_idx]):<12.4f} {float(recall_per_class[cls_idx]):<12.4f} {float(f1_per_class[cls_idx]):<10.4f}"
        )

    report_lines.extend([
        "-" * 74,
        "",
        "CONFUSION MATRIX (Rows: True Class, Columns: Predicted Class):",
        "--------------------------------------------------------------",
        f"{'':<20} " + " ".join(f"{name:>12}" for name in CLASS_NAMES),
    ])

    for row_idx, row in enumerate(cm):
        row_str = " ".join(f"{int(val):>12d}" for val in row)
        report_lines.append(f"{CLASS_NAMES[row_idx]:<20} {row_str}")

    report_lines.extend([
        "",
        "DISCLAIMER:",
        "-----------",
        "This evaluation report is generated for model testing and research purposes only.",
        "No medical diagnostic claims are made. Not for direct clinical diagnosis.",
        "==================================================================",
    ])

    with open(EVALUATION_REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines) + "\n")
    print(f"[OK] Saved evaluation report to: {EVALUATION_REPORT_PATH}")

    # 10. Print the exact required summary format
    print("\n" + "=" * 40)
    print("RETINAGUARD FINAL TEST EVALUATION")
    print("=" * 40)
    print(f"Checkpoint: Epoch {best_epoch}")
    print("Model: EfficientNet-B0")
    print(f"Test Samples: {num_test_samples}")
    print("")
    print(f"Test Accuracy: {accuracy:.4f}")
    print(f"Test Macro F1: {macro_f1:.4f}")
    print(f"Test Weighted F1: {weighted_f1:.4f}")
    print("")
    print(f"Correct Predictions: {correct_predictions}")
    print(f"Incorrect Predictions: {incorrect_predictions}")
    print("")
    print(f"Best Validation Macro F1: {best_val_f1:.4f}")
    print("")
    print("Confusion Matrix:")
    print(r"docs\test_confusion_matrix.png")
    print("")
    print("Evaluation Report:")
    print(r"docs\test_evaluation.txt")
    print("")
    print("Predictions:")
    print(r"docs\test_predictions.csv")
    print("")
    print("Test set was evaluated only after training was completed.")
    print("=" * 40)


if __name__ == "__main__":
    evaluate()
