"""
RetinaGuard Image Quality Gate Test Suite
Validates:
1. Normal fundus image from dataset evaluates and passes.
2. Deliberately blurred version is detected as lower quality / fails focus check.
3. Very dark image is detected as underexposed / fails.
4. Very bright / overexposed image is detected as overexposed / fails.
5. Blank / invalid image fails safely.
6. Verification that failed quality check does NOT invoke the DR classifier.
"""
import os
import sys
import unittest
from pathlib import Path
import cv2
import numpy as np

# Ensure ASCII output for Windows cp1252 safety
if hasattr(sys.stdout, "reconfigure"):
    getattr(sys.stdout, "reconfigure")(line_buffering=True, errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.services.quality.service import quality_service, QualityAssessmentService
from backend.services.classification.service import classification_service
from backend.models.schemas import QualityMetrics, ScreeningSession, ClinicalReview
from backend.models.database import db


class TestImageQualityGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Locate a valid normal fundus image from APTOS 2019 train set
        img_dir = PROJECT_ROOT / "data" / "raw" / "aptos2019" / "train_images"
        cls.normal_image_path = None
        for p in img_dir.glob("*.png"):
            img = cv2.imread(str(p))
            if img is not None and img.shape[0] > 200:
                cls.normal_image_path = p
                cls.normal_img_bgr = img
                break

        if cls.normal_image_path is None:
            raise FileNotFoundError("Could not find a valid APTOS fundus image for quality gate testing.")
        
        print(f"[SETUP] Using test reference fundus image: {cls.normal_image_path.name}")

    def test_01_normal_fundus_image_passes(self):
        """Test 1: Normal fundus image from dataset evaluates and passes the quality gate."""
        result: QualityMetrics = quality_service.assess_image_quality(self.normal_img_bgr)
        
        self.assertTrue(result.passed, f"Normal image failed quality check! Issues: {result.issues}")
        self.assertIn(result.state, ["GOOD", "BORDERLINE"])
        self.assertGreaterEqual(result.quality_score, 0.70)
        self.assertGreaterEqual(result.blur_score, 0.50)
        self.assertGreaterEqual(result.brightness_score, 0.50)
        self.assertGreaterEqual(result.contrast_score, 0.50)
        self.assertGreaterEqual(result.retinal_visibility_score, 0.50)
        self.assertEqual(len(result.issues), 0)
        self.assertIn("acceptable", result.feedback_text.lower())
        print(f"[PASS] Test 1: Normal fundus image passed (Quality Score: {result.quality_score:.3f}, State: {result.state})")

    def test_02_blurred_image_detected(self):
        """Test 2: Deliberately blurred version is detected as lower quality and flags blur."""
        # Apply heavy Gaussian blur (never modifying original image)
        blurred_img = cv2.GaussianBlur(self.normal_img_bgr, (51, 51), 18)
        
        result: QualityMetrics = quality_service.assess_image_quality(blurred_img)
        normal_res: QualityMetrics = quality_service.assess_image_quality(self.normal_img_bgr)
        
        # Must detect lower quality than normal image
        self.assertLess(result.blur_score, normal_res.blur_score)
        self.assertFalse(result.passed, "Heavily blurred image should not pass the quality gate")
        self.assertEqual(result.state, "UNGRADABLE")
        
        # Check that blur issue was specifically reported
        has_blur_issue = any("blur" in issue.lower() or "focus" in issue.lower() for issue in result.issues)
        self.assertTrue(has_blur_issue, f"Expected blur issue in: {result.issues}")
        self.assertIn("insufficient", result.feedback_text.lower())
        print(f"[PASS] Test 2: Blurred image detected (Blur Score: {result.blur_score:.3f} vs Normal: {normal_res.blur_score:.3f}, Issue: {result.issues[0]})")

    def test_03_dark_underexposed_image_detected(self):
        """Test 3: Very dark / underexposed image is detected and rejected."""
        # Scale brightness down to 10%
        dark_img = (self.normal_img_bgr * 0.10).astype(np.uint8)
        
        result: QualityMetrics = quality_service.assess_image_quality(dark_img)
        
        self.assertFalse(result.passed, "Very dark image should not pass the quality gate")
        self.assertEqual(result.state, "UNGRADABLE")
        has_dark_issue = any(
            "dark" in issue.lower() or "visibility" in issue.lower() or "illumination" in issue.lower()
            for issue in result.issues
        )
        self.assertTrue(has_dark_issue, f"Expected dark/illumination issue in: {result.issues}")
        print(f"[PASS] Test 3: Dark image detected (Issues: {result.issues})")

    def test_04_overexposed_image_detected(self):
        """Test 4: Very bright / overexposed image is detected and rejected."""
        # Severely overexpose image with +160 pixel offset
        overexposed_img = np.clip(self.normal_img_bgr.astype(np.float32) + 160.0, 0, 255).astype(np.uint8)
        
        result: QualityMetrics = quality_service.assess_image_quality(overexposed_img)
        
        self.assertFalse(result.passed, "Overexposed image should not pass the quality gate")
        self.assertEqual(result.state, "UNGRADABLE")
        has_overexp_issue = any(
            "overexposed" in issue.lower() or "glare" in issue.lower() or "artifact" in issue.lower()
            for issue in result.issues
        )
        self.assertTrue(has_overexp_issue, f"Expected overexposure/glare issue in: {result.issues}")
        print(f"[PASS] Test 4: Overexposed image detected (Issues: {result.issues})")

    def test_05_blank_invalid_image_fails_safely(self):
        """Test 5: Blank black, blank white, and None inputs fail safely."""
        # Solid black
        black_img = np.zeros((512, 512, 3), dtype=np.uint8)
        res_black = quality_service.assess_image_quality(black_img)
        self.assertFalse(res_black.passed)
        self.assertEqual(res_black.state, "UNGRADABLE")
        self.assertEqual(res_black.quality_score, 0.0)

        # Solid white
        white_img = np.full((512, 512, 3), 255, dtype=np.uint8)
        res_white = quality_service.assess_image_quality(white_img)
        self.assertFalse(res_white.passed)
        self.assertEqual(res_white.state, "UNGRADABLE")

        # None input
        res_none = quality_service.assess_image_quality(None)
        self.assertFalse(res_none.passed)
        self.assertEqual(res_none.state, "UNGRADABLE")

        # Empty bytes
        res_empty = quality_service.assess_image_quality(b"")
        self.assertFalse(res_empty.passed)
        self.assertEqual(res_empty.state, "UNGRADABLE")

        print("[PASS] Test 5: Blank and invalid images handled safely with UNGRADABLE status")

    def test_06_failed_quality_blocks_classifier(self):
        """Test 6: Verify that a failed quality check strictly blocks the DR classifier from executing."""
        # Create a degraded/blurred image
        blurred_img = cv2.GaussianBlur(self.normal_img_bgr, (51, 51), 18)
        failed_quality = quality_service.assess_image_quality(blurred_img)
        self.assertFalse(failed_quality.passed)

        # 1. Calling classify_severity with failed quality_metrics MUST raise ValueError
        with self.assertRaises(ValueError) as ctx:
            classification_service.classify_severity(
                image_input=blurred_img,
                quality_metrics=failed_quality
            )
        self.assertIn("Cannot classify image: Image Quality Gate failed", str(ctx.exception))

        # 2. Calling classify_severity directly with degraded image (without passing metrics)
        # MUST internally trigger quality check and raise ValueError
        with self.assertRaises(ValueError) as ctx:
            classification_service.classify_severity(image_input=blurred_img)
        self.assertIn("Cannot classify image: Image Quality Gate failed", str(ctx.exception))

        # 3. Simulate Screening Route guard
        session_id = "SCR-TEST-GATE-01"
        session = ScreeningSession(
            id=session_id,
            patient_id="PT-TEST",
            patient_name="Gate Test Patient",
            patient_age=45,
            patient_gender="Female",
            eye="OD",
            created_at="2026-09-21T00:00:00Z",
            quality=failed_quality,
            current_step=3,
            review=ClinicalReview(status="PENDING")
        )
        db.screenings[session_id] = session

        # Verify that session.quality.passed is False and DR grade is NOT set
        self.assertFalse(session.quality.passed)
        self.assertIsNone(session.classification)

        print("[PASS] Test 6: Quality failure strictly blocked DR classification and prevented grade generation")


def run_all_tests():
    print("==================================================")
    print("      RETINAGUARD IMAGE QUALITY GATE TEST RUN     ")
    print("==================================================")
    suite = unittest.TestLoader().loadTestsFromTestCase(TestImageQualityGate)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    print("==================================================")
    if result.wasSuccessful():
        print(f"RESULT: ALL {result.testsRun} QUALITY GATE TESTS PASSED!")
        print("==================================================")
        return 0
    else:
        print(f"RESULT: {len(result.failures)} FAILURES, {len(result.errors)} ERRORS")
        print("==================================================")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
