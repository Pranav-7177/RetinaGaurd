"""
RetinaGuard Image Quality Assessment Service
Rule-based quality gate using measurable OpenCV image-processing criteria.
Assesses blur/focus, illumination/exposure, contrast, retinal visibility, and artifacts.
Evaluates images BEFORE preprocessing and BEFORE the DR classifier.
"""
from pathlib import Path
from typing import Union, Optional, List, Tuple
import cv2
import numpy as np

from ...models.schemas import QualityMetrics, QualityState


class QualityAssessmentService:
    """
    Measurable, rule-based image quality gate for retinal fundus images.
    Thresholds calibrated against APTOS 2019 fundus datasets.
    """

    # Threshold constants
    MIN_IMAGE_DIMENSION: int = 100
    MIN_RETINAL_VISIBILITY: float = 0.35     # Minimum ratio of foreground retina to image area
    MIN_BLUR_LAPLACIAN_VAR: float = 2.50    # Minimum Laplacian variance on green channel
    MIN_MEAN_BRIGHTNESS: float = 35.0        # Minimum mean intensity on retinal foreground
    MAX_MEAN_BRIGHTNESS: float = 180.0       # Maximum mean intensity on retinal foreground
    MIN_CONTRAST_STD: float = 8.00           # Minimum standard deviation on retinal foreground
    MAX_ARTIFACT_SATURATION_RATIO: float = 0.15  # Max proportion of saturated pixels (>248)

    def _load_image(
        self,
        image_input: Union[bytes, str, Path, np.ndarray, None]
    ) -> Optional[np.ndarray]:
        """
        Loads and decodes image input into a BGR numpy array.
        Supports raw bytes, file path (str/Path), or numpy array.
        """
        if image_input is None:
            return None

        if isinstance(image_input, np.ndarray):
            if image_input.size == 0:
                return None
            if len(image_input.shape) == 2:
                return cv2.cvtColor(image_input, cv2.COLOR_GRAY2BGR)
            return image_input

        if isinstance(image_input, (str, Path)):
            path = Path(image_input)
            if not path.exists() or not path.is_file():
                return None
            img = cv2.imread(str(path))
            return img

        if isinstance(image_input, bytes):
            if len(image_input) == 0:
                return None
            nparr = np.frombuffer(image_input, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return img

        return None

    def assess_image_quality(
        self,
        image_input: Union[bytes, str, Path, np.ndarray, None] = None,
        filename: str = ""
    ) -> QualityMetrics:
        """
        Assesses fundus image quality using measurable image processing rules.
        Returns a structured QualityMetrics object with scores, issues, and human-readable feedback.
        """
        # 1. Validate image load
        img = self._load_image(image_input)
        if img is None:
            return QualityMetrics(
                state="UNGRADABLE",
                passed=False,
                quality_score=0.0,
                overall_score=0.0,
                blur_score=0.0,
                focus_score=0.0,
                brightness_score=0.0,
                illumination_score=0.0,
                contrast_score=0.0,
                retinal_visibility_score=0.0,
                field_of_view_score=0.0,
                artifact_score=1.0,
                issues=["Invalid or unreadable image data. Please upload a valid image file (JPG, PNG)."],
                feedback_text="Image quality insufficient. Please recapture the fundus image.",
                enhancement_recommended=False,
                recapture_guidance=["Invalid or unreadable image data. Please upload a valid image file (JPG, PNG)."],
            )

        h, w = img.shape[:2]
        if h < self.MIN_IMAGE_DIMENSION or w < self.MIN_IMAGE_DIMENSION:
            return QualityMetrics(
                state="UNGRADABLE",
                passed=False,
                quality_score=0.05,
                overall_score=0.05,
                blur_score=0.0,
                focus_score=0.0,
                brightness_score=0.0,
                illumination_score=0.0,
                contrast_score=0.0,
                retinal_visibility_score=0.0,
                field_of_view_score=0.0,
                artifact_score=1.0,
                issues=[f"Image resolution too low ({w}x{h}). Minimum required is {self.MIN_IMAGE_DIMENSION}x{self.MIN_IMAGE_DIMENSION}."],
                feedback_text="Image quality insufficient. Please recapture the fundus image.",
                enhancement_recommended=False,
                recapture_guidance=[f"Image resolution too low ({w}x{h}). Minimum required is {self.MIN_IMAGE_DIMENSION}x{self.MIN_IMAGE_DIMENSION}."],
            )

        # 2. Extract channels and foreground retinal mask
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        green = img[:, :, 1]

        # Retinal foreground segmentation (fundus tissue is significantly brighter than camera border)
        mask = (gray > 15).astype(np.uint8)
        retina_pixels_count = int(np.sum(mask))
        total_pixels = mask.size
        vis_ratio = float(retina_pixels_count) / total_pixels

        issues: List[str] = []

        # 3. Retinal Visibility Check
        if vis_ratio < self.MIN_RETINAL_VISIBILITY:
            issues.append("Retinal region is not sufficiently visible. Please center the retina in the viewfinder and recapture.")
            retinal_vis_score = round(max(0.0, min(1.0, vis_ratio / 0.5)), 3)
        else:
            retinal_vis_score = round(min(1.0, vis_ratio / 0.75), 3)

        # If image is essentially blank or completely black, fail immediately
        if retina_pixels_count < 100:
            return QualityMetrics(
                state="UNGRADABLE",
                passed=False,
                quality_score=0.0,
                overall_score=0.0,
                blur_score=0.0,
                focus_score=0.0,
                brightness_score=0.0,
                illumination_score=0.0,
                contrast_score=0.0,
                retinal_visibility_score=retinal_vis_score,
                field_of_view_score=retinal_vis_score,
                artifact_score=1.0,
                issues=issues if issues else ["Image appears completely black or unexposed."],
                feedback_text="Image quality insufficient. Please recapture the fundus image.",
                enhancement_recommended=False,
                recapture_guidance=issues,
            )

        retina_gray = gray[mask > 0]

        # 4. Brightness / Illumination Check
        mean_brightness = float(np.mean(retina_gray))
        if mean_brightness < self.MIN_MEAN_BRIGHTNESS:
            issues.append("Image is too dark. Please improve illumination and recapture.")
            brightness_score = round(max(0.0, mean_brightness / self.MIN_MEAN_BRIGHTNESS * 0.5), 3)
        elif mean_brightness > self.MAX_MEAN_BRIGHTNESS:
            issues.append("Image is overexposed. Please adjust illumination and recapture.")
            excess = mean_brightness - self.MAX_MEAN_BRIGHTNESS
            brightness_score = round(max(0.0, 1.0 - (excess / 75.0)), 3)
        else:
            # Ideal range ~80-120
            diff_from_ideal = abs(mean_brightness - 100.0)
            brightness_score = round(max(0.70, 1.0 - (diff_from_ideal / 160.0)), 3)

        # 5. Contrast Check
        contrast_std = float(np.std(retina_gray))
        if contrast_std < self.MIN_CONTRAST_STD:
            issues.append("Image has insufficient contrast. Please check lens clarity and lighting balance.")
            contrast_score = round(max(0.0, contrast_std / self.MIN_CONTRAST_STD * 0.5), 3)
        else:
            contrast_score = round(min(1.0, 0.5 + (contrast_std / 35.0) * 0.5), 3)

        # 6. Blur / Focus Check (Variance of Laplacian on green channel within retinal bounds)
        x, y, bw, bh = cv2.boundingRect(mask)
        crop_green = green[y:y+bh, x:x+bw]
        laplacian_var = float(cv2.Laplacian(crop_green, cv2.CV_64F).var())

        if laplacian_var < self.MIN_BLUR_LAPLACIAN_VAR:
            issues.append("Image appears blurry. Please ensure camera focus is locked on the retina and recapture.")
            blur_score = round(max(0.0, laplacian_var / self.MIN_BLUR_LAPLACIAN_VAR * 0.5), 3)
        else:
            blur_score = round(min(1.0, 0.5 + (laplacian_var / 50.0) * 0.5), 3)

        # 7. Artifacts / Glare Check
        saturated_pixels = int(np.sum(retina_gray > 248))
        sat_ratio = float(saturated_pixels) / len(retina_gray)

        if sat_ratio > self.MAX_ARTIFACT_SATURATION_RATIO:
            issues.append("Image contains excessive artifacts or specular glare. Please adjust lens angle to eliminate glare and recapture.")
            artifact_score = round(min(1.0, sat_ratio / 0.30), 3)
        else:
            artifact_score = round(min(0.20, sat_ratio * 1.33), 3)

        # 8. Compute Overall Quality Score & Status
        # Overall quality is a weighted harmonic/geometric combination of criteria
        quality_score = round(
            0.25 * blur_score +
            0.20 * brightness_score +
            0.20 * contrast_score +
            0.20 * retinal_vis_score +
            0.15 * (1.0 - artifact_score),
            3
        )

        passed = len(issues) == 0

        if passed:
            state: QualityState = "GOOD" if quality_score >= 0.75 else "BORDERLINE"
            feedback_text = "Image quality acceptable. Proceeding to DR screening."
        else:
            state: QualityState = "UNGRADABLE"
            feedback_text = "Image quality insufficient. Please recapture the fundus image."

        return QualityMetrics(
            state=state,
            passed=passed,
            quality_score=quality_score,
            overall_score=quality_score,
            blur_score=blur_score,
            focus_score=blur_score,
            brightness_score=brightness_score,
            illumination_score=brightness_score,
            contrast_score=contrast_score,
            retinal_visibility_score=retinal_vis_score,
            field_of_view_score=retinal_vis_score,
            artifact_score=artifact_score,
            issues=issues,
            feedback_text=feedback_text,
            enhancement_recommended=(state == "BORDERLINE" or contrast_score < 0.75),
            recapture_guidance=issues,
        )


quality_service = QualityAssessmentService()
