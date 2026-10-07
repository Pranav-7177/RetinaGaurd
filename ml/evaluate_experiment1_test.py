import argparse
from pathlib import Path
import sys

# Ensure ASCII / line-buffered stdout for Windows cp1252 terminal safety
if hasattr(sys.stdout, "reconfigure"):
    getattr(sys.stdout, "reconfigure")(line_buffering=True, errors="replace")

import matplotlib
matplotlib.use("Agg")
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
CHECKPOINT_PATH = MODELS_DIR / "retinaguard_exp1_best.pth"
DOCS_DIR = PROJECT_ROOT / "docs"

CONFUSION_MATRIX_PATH = DOCS_DIR / "experiment1_test_confusion_matrix.png"
REPORT_PATH = DOCS_DIR / "experiment1_test_evaluation.txt"
PREDICTIONS_CSV_PATH = DOCS_DIR / "experiment1_test_predictions.csv"

BATCH_SIZE = 16

CLASS_NAMES = [
    "No DR",
    "Mild NPDR",
    "Moderate NPDR",
    "Severe NPDR",
    "Proliferative DR",
]
NUM_CLASSES = len(CLASS_NAMES)

# Baseline TEST metrics (from docs/test_evaluation.txt)
BASELINE_TEST_METRICS = {
    "accuracy": 0.8023,
    "macro_f1": 0.6494,
    "weighted_f1": 0.8100,
    "correct": 422,
    "incorrect": 104,
    "total": 526,
    "per_class": {
        0: {"name": "No DR", "precision": 0.9886, "recall": 0.9667, "f1": 0.9775, "support": 270},
        1: {"name": "Mild NPDR", "precision": 0.5000, "recall": 0.7059, "f1": 0.5854, "support": 51},
        2: {"name": "Moderate NPDR", "precision": 0.7731, "recall": 0.6667, "f1": 0.7160, "support": 138},
        3: {"name": "Severe NPDR", "precision": 0.3191, "recall": 0.5556, "f1": 0.4054, "support": 27},
        4: {"name": "Proliferative DR", "precision": 0.7500, "recall": 0.4500, "f1": 0.5625, "support": 40},
    },
}


def get_device() -> torch.device:
    if torch.cuda.is_available():
        device = torch.device("cuda")
        print(f"Selected device: {device} ({torch.cuda.get_device_name(0)})")
    else:
        device = torch.device("cpu")
        print(f"Selected device: {device}")
    return device


def evaluate_test():
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Verify existence of required files
    if not TEST_CSV.exists():
        raise FileNotFoundError(f"Test CSV not found: {TEST_CSV}")
    if not CHECKPOINT_PATH.exists():
        raise FileNotFoundError(f"Checkpoint not found: {CHECKPOINT_PATH}")
    if not IMAGE_DIR.exists():
        raise FileNotFoundError(f"Image directory not found: {IMAGE_DIR}")

    device = get_device()

    # 2. Load Checkpoint
    checkpoint = torch.load(CHECKPOINT_PATH, map_location=device)
    ckpt_epoch = checkpoint.get("epoch", 8)
    best_val_f1 = float(checkpoint.get("best_val_f1", 0.0))
    num_classes = int(checkpoint.get("num_classes", NUM_CLASSES))

    # 3. Initialize Model and Load Weights
    model = create_model(num_classes=num_classes)
    model.load_state_dict(checkpoint["model_state_dict"])
    model = model.to(device)
    model.eval()

    # 4. Load Test Dataset (Strictly no augmentations)
    test_df = pd.read_csv(TEST_CSV)
    num_test_samples = len(test_df)

    test_dataset = RetinaDataset(
        csv_file=TEST_CSV,
        image_dir=IMAGE_DIR,
        training=False,
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=0,
        pin_memory=(device.type == "cuda"),
    )

    # 5. Inference with torch.no_grad()
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

    targets_arr = np.array(all_targets, dtype=int)
    preds_arr = np.array(all_preds, dtype=int)

    # 6. Calculate Metrics
    accuracy = float(accuracy_score(targets_arr, preds_arr))
    macro_f1 = float(f1_score(targets_arr, preds_arr, average="macro", zero_division=0))
    weighted_f1 = float(f1_score(targets_arr, preds_arr, average="weighted", zero_division=0))
    correct_predictions = int(np.sum(targets_arr == preds_arr))
    incorrect_predictions = int(num_test_samples - correct_predictions)

    prf_res = precision_recall_fscore_support(
        targets_arr, preds_arr, labels=list(range(NUM_CLASSES)), zero_division=0
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
    plt.title(f"Experiment 1 Test Confusion Matrix (Epoch {ckpt_epoch})", fontsize=12, pad=15)
    plt.xlabel("Predicted Class", fontsize=11, labelpad=10)
    plt.ylabel("True Class", fontsize=11, labelpad=10)
    plt.xticks(rotation=30, ha="right")
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(CONFUSION_MATRIX_PATH, dpi=300)
    plt.close()

    # 9. Comparison with Baseline Test Metrics
    acc_diff = accuracy - BASELINE_TEST_METRICS["accuracy"]
    macro_f1_diff = macro_f1 - BASELINE_TEST_METRICS["macro_f1"]
    weighted_f1_diff = weighted_f1 - BASELINE_TEST_METRICS["weighted_f1"]
    correct_diff = correct_predictions - BASELINE_TEST_METRICS["correct"]

    # 10. Generate Evaluation Report Text
    report_lines = [
        "==================================================================",
        "             RETINAGUARD EXPERIMENT 1 TEST EVALUATION",
        "==================================================================",
        "",
        "EXPERIMENT INFORMATION:",
        "-----------------------",
        "Experiment 1 Test Evaluation",
        "Checkpoint: models/retinaguard_exp1_best.pth",
        f"Checkpoint epoch: {ckpt_epoch}",
        "Test set: data/processed/test.csv",
        f"Test set size: {num_test_samples}",
        "Test set was not used during training or model selection.",
        "",
        "OVERALL TEST METRICS:",
        "---------------------",
        f"Test Accuracy:            {accuracy:.4f} ({accuracy * 100:.2f}%)",
        f"Test Macro F1:            {macro_f1:.4f} ({macro_f1 * 100:.2f}%)",
        f"Test Weighted F1:         {weighted_f1:.4f} ({weighted_f1 * 100:.2f}%)",
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
        "                            " + " ".join([f"{CLASS_NAMES[i][:12]:>14}" for i in range(NUM_CLASSES)]),
    ])

    for i in range(NUM_CLASSES):
        row_vals = " ".join([f"{cm[i, j]:>14d}" for j in range(NUM_CLASSES)])
        report_lines.append(f"{CLASS_NAMES[i]:<28}{row_vals}")

    report_lines.extend([
        "",
        "BASELINE VS EXPERIMENT 1 TEST COMPARISON:",
        "-----------------------------------------",
        f"Metric               Baseline TEST        Experiment 1 TEST    Delta",
        "-" * 70,
        f"Accuracy:            {BASELINE_TEST_METRICS['accuracy']*100:6.2f}%              {accuracy*100:6.2f}%             {acc_diff*100:+6.2f}%",
        f"Macro F1:            {BASELINE_TEST_METRICS['macro_f1']*100:6.2f}%              {macro_f1*100:6.2f}%             {macro_f1_diff*100:+6.2f}%",
        f"Weighted F1:         {BASELINE_TEST_METRICS['weighted_f1']*100:6.2f}%              {weighted_f1*100:6.2f}%             {weighted_f1_diff*100:+6.2f}%",
        f"Correct / Total:     {BASELINE_TEST_METRICS['correct']}/{num_test_samples} ({BASELINE_TEST_METRICS['correct']/num_test_samples*100:.1f}%)        {correct_predictions}/{num_test_samples} ({correct_predictions/num_test_samples*100:.1f}%)       {correct_diff:+4d}",
        "-" * 70,
        "",
        "PER-CLASS F1 COMPARISON:",
        "------------------------",
        f"{'Class ID & Name':<22} | {'Baseline F1':<14} | {'Exp 1 F1':<14} | {'F1 Delta':<10}",
        "-" * 68,
    ])

    for c in range(NUM_CLASSES):
        b_f1 = BASELINE_TEST_METRICS["per_class"][c]["f1"]
        e_f1 = float(f1_per_class[c])
        delta = e_f1 - b_f1
        report_lines.append(
            f"{c}: {CLASS_NAMES[c]:<19} | {b_f1:<14.4f} | {e_f1:<14.4f} | {delta:+10.4f}"
        )

    report_lines.extend([
        "-" * 68,
        "",
        "DISCLAIMER:",
        "-----------",
        "This evaluation report is generated for model testing and research purposes only.",
        "No medical diagnostic claims are made. Not for direct clinical diagnosis.",
        "==================================================================",
    ])

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines) + "\n")

    # 11. Print Required Clean ASCII Terminal Summary
    print("========================================")
    print("RETINAGUARD EXPERIMENT 1 TEST RESULTS")
    print("========================================")
    print("")
    print(f"Checkpoint: Epoch {ckpt_epoch}")
    print(f"Test Samples: {num_test_samples}")
    print("")
    print(f"Test Accuracy:    {accuracy * 100:.2f}%")
    print(f"Test Macro F1:    {macro_f1 * 100:.2f}%")
    print(f"Test Weighted F1: {weighted_f1 * 100:.2f}%")
    print("")
    print(f"Correct:   {correct_predictions} / {num_test_samples}")
    print(f"Incorrect: {incorrect_predictions} / {num_test_samples}")
    print("")
    print("Per-Class Metrics:")
    for cls_idx in range(NUM_CLASSES):
        print(
            f"Class {cls_idx} ({CLASS_NAMES[cls_idx]}): Precision: {precision_per_class[cls_idx]:.4f} | "
            f"Recall: {recall_per_class[cls_idx]:.4f} | F1: {f1_per_class[cls_idx]:.4f} | Support: {int(support_per_class[cls_idx])}"
        )
    print("")
    print("Confusion Matrix:")
    header = "       " + " ".join([f"{CLASS_NAMES[i][:7]:>8}" for i in range(NUM_CLASSES)])
    print(header)
    for i in range(NUM_CLASSES):
        row = f"Cls {i}: " + " ".join([f"{cm[i, j]:>8d}" for j in range(NUM_CLASSES)])
        print(row)
    print("")
    print("BASELINE VS EXPERIMENT 1:")
    print(f"Accuracy:    Baseline {BASELINE_TEST_METRICS['accuracy']*100:.2f}% -> Exp 1 {accuracy*100:.2f}% ({acc_diff*100:+.2f}%)")
    print(f"Macro F1:    Baseline {BASELINE_TEST_METRICS['macro_f1']*100:.2f}% -> Exp 1 {macro_f1*100:.2f}% ({macro_f1_diff*100:+.2f}%)")
    print(f"Weighted F1: Baseline {BASELINE_TEST_METRICS['weighted_f1']*100:.2f}% -> Exp 1 {weighted_f1*100:.2f}% ({weighted_f1_diff*100:+.2f}%)")
    print("========================================")


if __name__ == "__main__":
    evaluate_test()
