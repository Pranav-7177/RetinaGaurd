# RetinaGuard End-to-End Screening Pipeline Documentation

This document describes the actual implemented end-to-end Diabetic Retinopathy (DR) screening pipeline connecting the trained EfficientNet-B0 deep learning classifier to the RetinaGuard FastAPI backend and clinical user interface.

---

## 1. Pipeline Overview

```
[Fundus Photograph (RGB)]
           │
           ▼
[Rule-Based Image Quality Gate]
  ├── Blur & Focus Assessment (Laplacian Variance >= 2.50)
  ├── Exposure & Illumination Check (Retinal Foreground Mean 35.0 - 180.0)
  ├── Contrast Standard Deviation Check (Foreground Std >= 8.00)
  ├── Retinal Field-of-View & Foreground Visibility (>= 35% FOV)
  └── Artifact & Specular Glare Threshold (<= 15% Saturated Pixels)
           │
     ┌─────┴────────────────┐
     │                      │
[FAILS Quality Gate]   [PASSES Quality Gate]
     │                      │
     ▼                      ▼
• Stop Processing       • Contrast Limited Adaptive Histogram Equalization (CLAHE)
• HTTP 400 Bad Request  • Input Tensor Normalization (224x224 RGB, ImageNet Mean/Std)
• Structured Issues &   • EfficientNet-B0 Forward Pass (eval mode, torch.no_grad)
  Recapture Guidance    • Softmax Probabilities across 5 DR Classes
• DR Classifier NOT     • Predicted DR Grade (0 to 4) & Maximum Confidence
  executed              • Clinical Referral Determination (Grade >= 2 Referable)
                        • Patient Screening History Record Updated
                        • Complete Result returned to UI
```

---

## 2. Component Specifications

### 2.1 Rule-Based Image Quality Gate
- **Location**: `backend/services/quality/service.py`
- **Method**: Measurable, deterministic OpenCV rules executed on raw unaugmented fundus image before any inference.
- **Enforcement Rules**:
  1. **Blur/Focus**: Green channel cropped to retinal mask; `cv2.Laplacian(green, cv2.CV_64F).var() >= 2.50`.
  2. **Brightness/Illumination**: Mean pixel intensity on foreground retina must fall within `[35.0, 180.0]`.
  3. **Contrast**: Standard deviation of retinal foreground pixels must be `>= 8.00`.
  4. **Retinal Visibility**: Foreground mask `(gray > 15)` pixel count ratio to total image area must be `>= 0.35`.
  5. **Specular Glare/Artifacts**: Saturated foreground pixels (`> 248`) must not exceed `15%`.
- **Quality Gate Failure Response**:
  - Immediately halts execution.
  - Returns **HTTP 400 Bad Request** with detailed rejection issues and actionable recapture guidance.
  - The DR classifier is strictly **not** executed.

### 2.2 CLAHE Preprocessing
- **Location**: `backend/services/preprocessing/service.py`
- **Method**: Adaptive Contrast Limited Adaptive Histogram Equalization (CLAHE) with tile grid size `(8, 8)` and clip limit `2.0`.
- **Output**: Generates enhanced contrast fundus preview for clinical visualization.

### 2.3 Deep Learning DR Classifier (EfficientNet-B0)
- **Location**: `backend/services/classification/service.py`
- **Model Checkpoint**: `models/retinaguard_exp1_best.pth` (Experiment 1, Best Epoch 8)
- **Architecture**: PyTorch `torchvision.models.efficientnet_b0` with classifier replaced:
  `Linear(in_features=1280, out_features=5)`
- **Inference Configuration**:
  - Loaded once into memory as a singleton (`self._model`).
  - Safe CPU execution fallback if GPU/CUDA is unavailable (`map_location=device`).
  - Evaluated under `model.eval()` and `torch.no_grad()`.
  - Normalization:
    - Input size: `224 x 224`
    - Channels: `RGB` (OpenCV BGR decoded image converted to RGB)
    - Mean: `[0.485, 0.456, 0.406]`
    - Standard Deviation: `[0.229, 0.224, 0.225]`
- **Official Untouched Test Set Evaluation Metrics**:
  - Test Accuracy: **81.75%** (430 / 526 correct)
  - Test Macro F1: **66.92%**
  - Test Weighted F1: **81.94%**

### 2.4 DR Grading System & Non-Diagnostic Clinical Referral Logic

| Class ID | Human-Readable DR Label | Referral Status | Referral Wording / Recommendation |
| :---: | :--- | :---: | :--- |
| **0** | **No DR** | `False` | Routine annual screening recommended; no immediate specialist referral required. |
| **1** | **Mild NPDR** | `False` | Routine screening recommended at 6-12 months; no immediate referral required. |
| **2** | **Moderate NPDR** | `True` | Referral recommended for tele-ophthalmology or clinical evaluation within 4-6 weeks. |
| **3** | **Severe NPDR** | `True` | Referral recommended for prompt ophthalmologist evaluation within 2-4 weeks. |
| **4** | **Proliferative DR** | `True` | Urgent specialist referral recommended: high suspicion of proliferative diabetic retinopathy requiring immediate ophthalmologist evaluation. |

> [!NOTE]
> All automated outputs denote screening triage recommendations and do not assert definitive diagnostic certainty or make treatment recommendations.

### 2.5 Patient Screening Record Integration
- **Constraint**: One screening event = one fundus photograph.
- **Patient Association**: The screening event is linked to the existing patient (`db.patients`). No patient is auto-created.
- **Audit Updating**: Updates `patient.screenings_count += 1`, `patient.last_screening_date`, `patient.last_dr_grade`, and `patient.is_referral_active`.
- **Eye-Side Tracking**: Preserves optional examined eye metadata (`OD` for Right Eye, `OS` for Left Eye, `NOT_SPECIFIED`). If both eyes are examined, they are stored as separate screening events without merging diagnostic grades.

---

## 3. Demarcation: Implemented vs. Future Research Features

| Feature | Pipeline Status | Implementation Details |
| :--- | :---: | :--- |
| **Rule-Based Quality Gate** | **Implemented** | Real OpenCV image metrics (blur, contrast, brightness, glare, visibility) with strict HTTP 400 enforcement. |
| **EfficientNet-B0 DR Classifier** | **Implemented** | Genuine checkpoint `retinaguard_exp1_best.pth`, eval mode, Softmax probabilities for all 5 grades. |
| **Referral Flag & Messaging** | **Implemented** | Grade >= 2 referral threshold with non-diagnostic triage messaging. |
| **Patient Record Appending** | **Implemented** | Association with registered patient and real-time history update. |
| **Single Image Upload Workflow** | **Implemented** | 1 screening = 1 fundus photograph with optional OD/OS/NOT_SPECIFIED metadata. |
| **Grad-CAM Saliency Heatmaps** | *Research Feature* | Prototype visualization heuristic demonstrating explainability interface. |
| **Microvascular Lesion Detection** | *Research Feature* | Visual indicator overlays for microaneurysms, hemorrhages, and hard exudates. |
| **District Capacity Simulator** | **Implemented** | Mathematical queuing model calculating throughput and doctor utilization. |
