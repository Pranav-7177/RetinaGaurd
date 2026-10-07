"""
Diabetic Retinopathy Classification Service
Runs inference using the final trained EfficientNet-B0 model (models/retinaguard_exp1_best.pth).
Strictly guarded by the Image Quality Gate: will reject classification if image quality fails.
"""
from pathlib import Path
from typing import Union, Optional, cast
import logging
import cv2
import numpy as np
import torch
import torch.nn.functional as F
from torchvision import transforms

from ...models.schemas import DRClassification, QualityMetrics, DRGrade
from ..quality.service import quality_service
from ...utils.logger import logger

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
MODELS_DIR = PROJECT_ROOT / "models"
CHECKPOINT_PATH = MODELS_DIR / "retinaguard_exp1_best.pth"

DR_LABELS = {
    0: "No DR",
    1: "Mild NPDR",
    2: "Moderate NPDR",
    3: "Severe NPDR",
    4: "Proliferative DR",
}

# Detailed clinical descriptions for backward compatibility
DR_GRADE_NAMES = {
    0: "No DR",
    1: "Mild NPDR",
    2: "Moderate NPDR",
    3: "Severe NPDR",
    4: "Proliferative DR",
}

DR_KEY_FINDINGS = {
    0: ["No microaneurysms or retinal hemorrhages detected.", "Retinal vasculature appears healthy."],
    1: ["Isolated microaneurysms detected in vascular arcade.", "No significant hard or soft exudates."],
    2: ["Multiple microaneurysms and intraretinal hemorrhages observed.", "Hard exudates present in macular region."],
    3: ["Severe intraretinal microvascular abnormalities (IRMA) detected.", "Extensive retinal hemorrhages in multiple quadrants."],
    4: ["Neovascularization on retinal surface or optic disc.", "Preretinal or vitreous hemorrhages identified."],
}

REFERRAL_MESSAGES = {
    0: "Routine annual screening recommended; no immediate specialist referral required.",
    1: "Routine screening recommended at 6-12 months; no immediate referral required.",
    2: "Referral recommended for tele-ophthalmology or clinical evaluation within 4-6 weeks.",
    3: "Referral recommended for prompt ophthalmologist evaluation within 2-4 weeks.",
    4: "Urgent specialist referral recommended: high suspicion of proliferative diabetic retinopathy requiring immediate ophthalmologist evaluation.",
}


class DRClassificationService:
    def __init__(self):
        self._model: Optional[torch.nn.Module] = None
        self._device: Optional[torch.device] = None
        # Preprocessing transforms matching the training/evaluation pipeline (224x224, ImageNet normalize)
        self._transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            ),
        ])

    def _get_device(self) -> torch.device:
        """Detect and return CUDA device if available, otherwise CPU."""
        if self._device is None:
            self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            logger.info(f"DRClassificationService device selected: {self._device}")
        return self._device

    def _load_model(self) -> torch.nn.Module:
        """
        Loads the final EfficientNet-B0 model checkpoint ONCE into memory.
        Subsequent calls reuse the cached self._model singleton.
        """
        if self._model is not None:
            return self._model

        if not CHECKPOINT_PATH.exists():
            err_msg = f"Model checkpoint file not found at: {CHECKPOINT_PATH}"
            logger.error(err_msg)
            raise FileNotFoundError(err_msg)

        import sys
        ml_path = PROJECT_ROOT / "ml"
        if str(ml_path) not in sys.path:
            sys.path.insert(0, str(ml_path))

        try:
            from model import create_model  # type: ignore
        except ImportError as exc:
            logger.error(f"Failed to import create_model from ml/model.py: {exc}")
            raise RuntimeError(f"Could not initialize model architecture: {exc}") from exc

        device = self._get_device()

        try:
            logger.info(f"Loading final EfficientNet-B0 checkpoint from {CHECKPOINT_PATH} onto {device}...")
            model = create_model(num_classes=5)
            checkpoint = torch.load(CHECKPOINT_PATH, map_location=device)
            state_dict = checkpoint.get("model_state_dict", checkpoint)
            model.load_state_dict(state_dict)
            model = model.to(device)
            model.eval()
            self._model = model
            logger.info(f"Model successfully loaded and initialized in eval mode (Epoch: {checkpoint.get('epoch', 'N/A')}).")
            return self._model
        except Exception as exc:
            logger.error(f"Failed loading model state dictionary: {exc}")
            raise RuntimeError(f"Failed to load DR classifier weights: {str(exc)}") from exc

    def classify_severity(
        self,
        image_input: Union[bytes, str, Path, np.ndarray, None] = None,
        quality_metrics: Optional[QualityMetrics] = None,
    ) -> DRClassification:
        """
        Classifies diabetic retinopathy severity into 5 standard grades (0-4).
        Strictly guarded by the Image Quality Gate:
        If quality check fails or is ungradable, classification is BLOCKED.
        """
        # 1. Image Quality Gate Enforcement: Check passed metrics
        if quality_metrics is not None and not quality_metrics.passed:
            issues_str = "; ".join(quality_metrics.issues) if quality_metrics.issues else "Quality check failed"
            logger.warning(f"DR Classification blocked by provided QualityMetrics: {issues_str}")
            raise ValueError(
                f"Cannot classify image: Image Quality Gate failed. {quality_metrics.feedback_text} (Issues: {issues_str})"
            )

        # 2. Image Quality Gate Enforcement: Check image directly if metrics not pre-computed
        if image_input is not None and quality_metrics is None:
            assessed_quality = quality_service.assess_image_quality(image_input)
            if not assessed_quality.passed:
                issues_str = "; ".join(assessed_quality.issues) if assessed_quality.issues else "Quality check failed"
                logger.warning(f"DR Classification blocked by dynamic quality assessment: {issues_str}")
                raise ValueError(
                    f"Cannot classify image: Image Quality Gate failed. {assessed_quality.feedback_text} (Issues: {issues_str})"
                )

        # 3. Handle null/missing image input
        if image_input is None:
            logger.warning("No image provided to classify_severity; raising error.")
            raise ValueError("Cannot classify image: No image input provided.")

        # 4. Load and validate image data
        img_bgr = quality_service._load_image(image_input)
        if img_bgr is None:
            logger.error("Failed to decode image input into a valid image matrix.")
            raise ValueError("Cannot classify image: Failed to load valid image data. Image may be corrupted or in an unsupported format.")

        h, w = img_bgr.shape[:2]
        if h < 100 or w < 100:
            raise ValueError(f"Cannot classify image: Image dimensions ({w}x{h}) are too small. Minimum dimension is 100x100.")

        # 5. Preprocess image matching training/eval pipeline:
        # OpenCV loads BGR -> convert to RGB -> 224x224 -> ToTensor -> Normalize
        try:
            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            tensor = self._transform(img_rgb).unsqueeze(0)  # Shape: [1, 3, 224, 224]
        except Exception as exc:
            logger.error(f"Image preprocessing failed: {exc}")
            raise ValueError(f"Failed to preprocess image for classification: {str(exc)}") from exc

        # 6. Model Inference
        model = self._load_model()
        device = self._get_device()
        tensor = tensor.to(device)

        try:
            with torch.no_grad():
                outputs = model(tensor)
                probs = F.softmax(outputs, dim=1).squeeze(0).cpu().numpy()
        except Exception as exc:
            logger.error(f"Inference execution failed: {exc}")
            raise RuntimeError(f"DR model inference failed during execution: {str(exc)}") from exc

        # 7. Extract predicted class, confidence, and class probabilities
        predicted_grade = int(np.argmax(probs))
        confidence = round(float(probs[predicted_grade]), 4)
        grade: DRGrade = cast(DRGrade, predicted_grade if predicted_grade in (0, 1, 2, 3, 4) else 0)

        # Referral logic: predicted_class >= 2 is referable
        is_referable = grade >= 2
        dr_label = DR_LABELS.get(grade, f"DR Grade {grade}")
        referral_msg = REFERRAL_MESSAGES.get(grade, "Referral recommended" if is_referable else "Routine screening recommended.")

        class_probabilities = {
            "Level 0 (No DR)": round(float(probs[0]), 4),
            "Level 1 (Mild NPDR)": round(float(probs[1]), 4),
            "Level 2 (Moderate NPDR)": round(float(probs[2]), 4),
            "Level 3 (Severe NPDR)": round(float(probs[3]), 4),
            "Level 4 (Proliferative DR)": round(float(probs[4]), 4),
        }

        return DRClassification(
            grade=grade,
            grade_name=dr_label,
            predicted_class=grade,
            dr_label=dr_label,
            referable=is_referable,
            referral_message=referral_msg,
            confidence=confidence,
            class_probabilities=class_probabilities,
            key_findings_summary=DR_KEY_FINDINGS.get(grade, ["Retinal assessment completed."]),
        )


classification_service = DRClassificationService()
