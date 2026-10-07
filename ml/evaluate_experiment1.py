import argparse
from pathlib import Path
import sys

# Ensure line-buffered stdout
if hasattr(sys.stdout, "reconfigure"):
    getattr(sys.stdout, "reconfigure")(line_buffering=True)

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

VAL_CSV = PROJECT_ROOT / "data" / "processed" / "validation.csv"
IMAGE_DIR = PROJECT_ROOT / "data" / "raw" / "aptos2019" / "train_images"
MODELS_DIR = PROJECT_ROOT / "models"
CHECKPOINT_PATH = MODELS_DIR / "retinaguard_exp1_best.pth"
DOCS_DIR = PROJECT_ROOT / "docs"
REPORT_PATH = DOCS_DIR / "experiment1_class_weighting.txt"
CONF_MATRIX_PATH = DOCS_DIR / "experiment1_val_confusion_matrix.png"

CLASS_NAMES = [
    "No DR",
    "Mild NPDR",
    "Moderate NPDR",
    "Severe NPDR",
    "Proliferative DR",
]
NUM_CLASSES = len(CLASS_NAMES)
BATCH_SIZE = 16

# Baseline metrics (Epoch 6) on validation set
BASELINE_METRICS = {
    "epoch": 6,
    "accuracy": 0.8156,
    "macro_f1": 0.6777,
    "weighted_f1": 0.8187,
    "per_class": {
        0: {"name": "No DR", "precision": 0.9776, "recall": 0.9740, "f1": 0.9758, "support": 269},
        1: {"name": "Mild NPDR", "precision": 0.4800, "recall": 0.7059, "f1": 0.5714, "support": 51},
        2: {"name": "Moderate NPDR", "precision": 0.7680, "recall": 0.6906, "f1": 0.7273, "support": 139},
        3: {"name": "Severe NPDR", "precision": 0.4688, "recall": 0.5769, "f1": 0.5172, "support": 26},
        4: {"name": "Proliferative DR", "precision": 0.7692, "recall": 0.4878, "f1": 0.5970, "support": 41},
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


def run_evaluation(log_path: Path | None = None):
    print("==================================================================")
    print("     RETINAGUARD EXPERIMENT 1: VALIDATION EVALUATION & REPORT")
    print("==================================================================")

    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    if not VAL_CSV.exists():
        raise FileNotFoundError(f"Validation CSV not found: {VAL_CSV}")
    if not CHECKPOINT_PATH.exists():
        raise FileNotFoundError(f"Checkpoint not found: {CHECKPOINT_PATH}")

    device = get_device()

    print(f"\nLoading Experiment 1 best checkpoint from: {CHECKPOINT_PATH}")
    checkpoint = torch.load(CHECKPOINT_PATH, map_location=device)
    best_epoch = checkpoint.get("epoch", "Unknown")
    best_val_f1_ckpt = float(checkpoint.get("best_val_f1", 0.0))
    num_classes = int(checkpoint.get("num_classes", NUM_CLASSES))

    print(f"Checkpoint Epoch:         {best_epoch}")
    print(f"Stored Val Macro F1:      {best_val_f1_ckpt:.4f}")

    # Load Model
    model = create_model(num_classes=num_classes)
    model.load_state_dict(checkpoint["model_state_dict"])
    model = model.to(device)
    model.eval()
    print("[OK] Model weights loaded and set to eval mode.")

    # Validation DataLoader
    val_dataset = RetinaDataset(csv_file=VAL_CSV, image_dir=IMAGE_DIR, training=False)
    val_loader = DataLoader(
        val_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=0,
        pin_memory=(device.type == "cuda"),
    )

    all_targets: list[int] = []
    all_preds: list[int] = []
    all_probs: list[list[float]] = []

    print("\nRunning inference on validation set (526 samples)...")
    with torch.no_grad():
        for batch_idx, (images, targets) in enumerate(val_loader):
            images = images.to(device)
            outputs = model(images)
            probs = F.softmax(outputs, dim=1)
            _, preds = torch.max(probs, dim=1)

            all_targets.extend([int(t) for t in targets.cpu().numpy()])
            all_preds.extend([int(p) for p in preds.cpu().numpy()])
            all_probs.extend([[float(v) for v in row] for row in probs.cpu().numpy()])

    targets_arr = np.array(all_targets, dtype=int)
    preds_arr = np.array(all_preds, dtype=int)

    val_accuracy = float(accuracy_score(targets_arr, preds_arr))
    val_macro_f1 = float(f1_score(targets_arr, preds_arr, average="macro", zero_division=0))
    val_weighted_f1 = float(f1_score(targets_arr, preds_arr, average="weighted", zero_division=0))

    precision, recall, f1, support = precision_recall_fscore_support(
        targets_arr, preds_arr, labels=list(range(NUM_CLASSES)), zero_division=0
    )
    cm = confusion_matrix(targets_arr, preds_arr, labels=list(range(NUM_CLASSES)))

    # Parse training logs if log_path exists
    epoch_logs = []
    if log_path and log_path.exists():
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            log_text = f.read()
        import re
        epoch_pattern = re.compile(
            r"Epoch \[(\d+)/\d+\] \(LR: ([^,]+), Time: ([^\)]+)\)\n\s+Train Loss: ([\d\.]+) \| Train Acc: ([\d\.]+) \| Train Macro F1: ([\d\.]+)\n\s+Val   Loss: ([\d\.]+) \| Val   Acc: ([\d\.]+) \| Val   Macro F1: ([\d\.]+)"
        )
        for match in epoch_pattern.finditer(log_text):
            ep, lr, tm, tr_l, tr_a, tr_f1, vl_l, vl_a, vl_f1 = match.groups()
            epoch_logs.append({
                "epoch": int(ep),
                "lr": lr,
                "time": tm,
                "train_loss": float(tr_l),
                "train_acc": float(tr_a),
                "train_f1": float(tr_f1),
                "val_loss": float(vl_l),
                "val_acc": float(vl_a),
                "val_f1": float(vl_f1),
            })

    # Plot Confusion Matrix
    plt.figure(figsize=(8, 6))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=CLASS_NAMES,
        yticklabels=CLASS_NAMES,
        cbar=True,
    )
    plt.title(f"Experiment 1 Validation Confusion Matrix (Epoch {best_epoch})", fontsize=13, pad=12)
    plt.xlabel("Predicted Class", fontsize=11)
    plt.ylabel("True Class", fontsize=11)
    plt.tight_layout()
    plt.savefig(CONF_MATRIX_PATH, dpi=300)
    plt.close()
    print(f"[OK] Saved confusion matrix plot to: {CONF_MATRIX_PATH}")

    # Build report text
    decision = "CANDIDATE FOR FUTURE TESTING" if val_macro_f1 > 0.6777 else "REJECTED (DO NOT EVALUATE ON TEST SET)"

    report_lines = [
        "==========================================================================================",
        "          RETINAGUARD EXPERIMENT 1 REPORT: CONSERVATIVE CLASS-WEIGHTED LOSS               ",
        "==========================================================================================",
        "",
        "1. EXPERIMENT OVERVIEW & DESCRIPTION",
        "------------------------------------------------------------------------------------------",
        "Experiment Name:  Conservative Square-Root Class Weighting Strategy",
        "Objective:        Improve validation Macro F1 (Baseline Epoch 6: 0.6777) and boost minority",
        "                  DR classes (Mild NPDR, Severe NPDR, Proliferative DR) without sacrificing",
        "                  No DR specificity.",
        "Architecture:     EfficientNet-B0 (5 classes)",
        "Training Set:     data/processed/train.csv (2452 samples)",
        "Validation Set:   data/processed/validation.csv (526 samples)",
        "Test Set:         data/processed/test.csv (526 samples) - STRICTLY UNTOUCHED",
        "Checkpoint Used:  models/retinaguard_exp1_best.pth",
        "",
        "2. MATHEMATICAL JUSTIFICATION & CLASS WEIGHTS",
        "------------------------------------------------------------------------------------------",
        "Baseline (Aggressive Inverse Balanced):",
        "  Formula:        w_c = N / (K * n_c)",
        "  Weights:        Class 0: 0.3901, Class 1: 2.0780, Class 2: 0.7603, Class 3: 3.9548, Class 4: 2.5811",
        "  Ratio (Max/Min): 10.14x (Class 3 is weighted 10.14x higher than Class 0)",
        "  Problem:        Class 0 (51.3% of dataset) was down-weighted to 0.3901, causing gradient instability",
        "                  and false positive spillover into minority classes.",
        "",
        "Experiment 1 (Conservative Square-Root Frequency):",
        "  Formula:        w_c proportional to sqrt(N / n_c), normalized so sum(w_c) = K (5.0)",
        "  Weights:        Class 0: 0.4780, Class 1: 1.1032, Class 2: 0.6673, Class 3: 1.5219, Class 4: 1.2295",
        "  Ratio (Max/Min): 3.18x (Class 3 is weighted 3.18x higher than Class 0)",
        "  Advantages:     Variance-stabilizing (sampling variance scales as O(1/sqrt(n_c))).",
        "                  Preserves dominant Class 0 loss gradient (raised to 0.4780) while giving",
        "                  rare classes a healthy 2.3x - 3.2x relative boost over Class 0 without distortion.",
        "",
        "3. TRAINING LOGS PER EPOCH",
        "------------------------------------------------------------------------------------------",
        f"{'Epoch':<7} | {'LR':<9} | {'Train Loss':<10} | {'Train Acc':<10} | {'Train F1':<10} | {'Val Loss':<10} | {'Val Acc':<10} | {'Val F1':<10}",
        "-" * 88,
    ]

    for log in epoch_logs:
        report_lines.append(
            f"{log['epoch']:<7} | {log['lr']:<9} | {log['train_loss']:<10.4f} | {log['train_acc']*100:<9.2f}% | {log['train_f1']:<10.4f} | {log['val_loss']:<10.4f} | {log['val_acc']*100:<9.2f}% | {log['val_f1']:<10.4f}"
        )

    report_lines.extend([
        "-" * 88,
        "",
        "4. BEST EPOCH & VALIDATION SUMMARY COMPARISON",
        "------------------------------------------------------------------------------------------",
        f"Metric                      Baseline (Epoch 6)       Experiment 1 (Epoch {best_epoch})       Delta",
        "-" * 88,
        f"Validation Accuracy:        {BASELINE_METRICS['accuracy']*100:6.2f}%                 {val_accuracy*100:6.2f}%               {(val_accuracy - BASELINE_METRICS['accuracy'])*100:+6.2f}%",
        f"Validation Macro F1:        {BASELINE_METRICS['macro_f1']:6.4f}                  {val_macro_f1:6.4f}                {val_macro_f1 - BASELINE_METRICS['macro_f1']:+6.4f}",
        f"Validation Weighted F1:     {BASELINE_METRICS['weighted_f1']:6.4f}                  {val_weighted_f1:6.4f}                {val_weighted_f1 - BASELINE_METRICS['weighted_f1']:+6.4f}",
        "",
        "5. PER-CLASS VALIDATION PERFORMANCE COMPARISON",
        "------------------------------------------------------------------------------------------",
        f"{'Class ID & Name':<20} | {'Baseline (P / R / F1)':<24} | {'Exp 1 (P / R / F1)':<24} | {'F1 Delta':<9} | {'Support':<8}",
        "-" * 92,
    ])

    for c in range(NUM_CLASSES):
        base_p = BASELINE_METRICS["per_class"][c]["precision"]
        base_r = BASELINE_METRICS["per_class"][c]["recall"]
        base_f = BASELINE_METRICS["per_class"][c]["f1"]
        supp = int(support[c])
        exp_p = float(precision[c])
        exp_r = float(recall[c])
        exp_f = float(f1[c])
        delta_f = exp_f - base_f

        base_str = f"{base_p:.2f} / {base_r:.2f} / {base_f:.4f}"
        exp_str = f"{exp_p:.2f} / {exp_r:.2f} / {exp_f:.4f}"
        report_lines.append(
            f"{c}: {CLASS_NAMES[c]:<17} | {base_str:<24} | {exp_str:<24} | {delta_f:+7.4f}   | {supp:<8}"
        )

    report_lines.extend([
        "-" * 92,
        "",
        "6. VALIDATION CONFUSION MATRIX (5x5)",
        "------------------------------------------------------------------------------------------",
        "True \\ Pred        " + "  ".join([f"{CLASS_NAMES[i][:7]:>7}" for i in range(NUM_CLASSES)]),
        "-" * 60,
    ])

    for i in range(NUM_CLASSES):
        row_str = f"{i}: {CLASS_NAMES[i]:<14} " + "  ".join([f"{cm[i, j]:>7d}" for j in range(NUM_CLASSES)])
        report_lines.append(row_str)

    # Minority class analysis
    c1_delta = float(f1[1]) - BASELINE_METRICS["per_class"][1]["f1"]
    c3_delta = float(f1[3]) - BASELINE_METRICS["per_class"][3]["f1"]
    c4_delta = float(f1[4]) - BASELINE_METRICS["per_class"][4]["f1"]
    c0_delta = float(f1[0]) - BASELINE_METRICS["per_class"][0]["f1"]

    report_lines.extend([
        "",
        "7. DETAILED ANALYSIS",
        "------------------------------------------------------------------------------------------",
        f"a. Minority Class Performance (Mild, Severe, Proliferative):",
        f"   - Class 1 (Mild NPDR):        F1 changed by {c1_delta:+7.4f} (Baseline: {BASELINE_METRICS['per_class'][1]['f1']:.4f} -> Exp 1: {float(f1[1]):.4f})",
        f"   - Class 3 (Severe NPDR):      F1 changed by {c3_delta:+7.4f} (Baseline: {BASELINE_METRICS['per_class'][3]['f1']:.4f} -> Exp 1: {float(f1[3]):.4f})",
        f"   - Class 4 (Proliferative DR): F1 changed by {c4_delta:+7.4f} (Baseline: {BASELINE_METRICS['per_class'][4]['f1']:.4f} -> Exp 1: {float(f1[4]):.4f})",
        "",
        f"b. Dominant Class (No DR) Impact:",
        f"   - Class 0 F1 changed by {c0_delta:+7.4f} (Baseline: {BASELINE_METRICS['per_class'][0]['f1']:.4f} -> Exp 1: {float(f1[0]):.4f})",
        f"   - Precision: {float(precision[0]):.4f}, Recall: {float(recall[0]):.4f}",
        "",
        f"c. Overall Macro F1 Impact:",
        f"   - Macro F1 changed by {val_macro_f1 - BASELINE_METRICS['macro_f1']:+7.4f} (Baseline: {BASELINE_METRICS['macro_f1']:.4f} -> Exp 1: {val_macro_f1:.4f})",
        "",
        "8. FINAL RECOMMENDATION & MODEL SELECTION DECISION",
        "------------------------------------------------------------------------------------------",
        f"Status: {decision}",
        f"Rule Applied: Strict rule that test set evaluation is ONLY allowed if validation Macro F1",
        f"              strictly beats baseline 0.6777.",
        f"Conclusion:   " + (
            f"Experiment 1 achieved {val_macro_f1:.4f} > 0.6777. Recommended for candidate pool."
            if val_macro_f1 > 0.6777 else
            f"Experiment 1 achieved {val_macro_f1:.4f} <= 0.6777. The baseline Epoch 6 checkpoint (0.6777) is RETAINED as the final model candidate. DO NOT evaluate on test set."
        ),
        "==========================================================================================",
    ])

    report_content = "\n".join(report_lines)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f"\n[OK] Successfully generated report: {REPORT_PATH}")
    print("\nReport preview:")
    print("\n".join(report_lines[:40]))
    print("...")
    print("\n".join(report_lines[-25:]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate Experiment 1 on validation set")
    parser.add_argument("--log-path", type=str, default=None, help="Path to training log file")
    args = parser.parse_args()

    log_p = Path(args.log_path) if args.log_path else None
    run_evaluation(log_p)
