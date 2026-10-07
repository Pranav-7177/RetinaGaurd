"""
RetinaGuard Final Model Integration Test Suite
Validates the complete end-to-end integration of the final EfficientNet-B0 model:
- Checkpoint: models/retinaguard_exp1_best.pth (Epoch 8)
- Gated strictly by Image Quality Gate

Tests:
A. Valid acceptable fundus image: quality passes and classifier executes.
B. Poor-quality image: quality fails (HTTP 400) and classifier is NOT executed.
C. Valid image: prediction contains predicted_class, dr_label, confidence, 5 class_probabilities, and referral status.
D. Invalid/corrupted image: safe error response (HTTP 400).
E. Model loading: verify the checkpoint loads successfully once into eval mode.
"""
import sys
import unittest
from pathlib import Path
import io
import cv2
import numpy as np

# Ensure ASCII output for Windows cp1252 safety
if hasattr(sys.stdout, "reconfigure"):
    getattr(sys.stdout, "reconfigure")(line_buffering=True, errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from backend.main import app
from backend.models.database import db
from backend.models.schemas import Patient
from backend.services.classification.service import classification_service, CHECKPOINT_PATH


class TestFinalModelIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

        # Locate a valid normal fundus image from APTOS 2019 dataset
        img_dir = PROJECT_ROOT / "data" / "raw" / "aptos2019" / "train_images"
        cls.sample_image_bytes = b""
        cls.sample_filename = ""
        for p in img_dir.glob("*.png"):
            with open(p, "rb") as f:
                content = f.read()
                if len(content) > 10000:
                    cls.sample_image_bytes = content
                    cls.sample_filename = p.name
                    break

        if not cls.sample_image_bytes:
            raise FileNotFoundError("Could not find a valid APTOS fundus image for test suite.")

        # Register a test patient in the database
        cls.patient_id = "PT-EXP1-TEST-001"
        test_patient = Patient(
            id=cls.patient_id,
            name="Rajendra Verma",
            age=58,
            gender="Male",
            phone="+91 98765 00001",
            district="Guntur",
            diabetes_type="Type 2",
            diabetes_duration_years=10,
            screenings_count=0,
            registered_at="2026-02-01T10:00:00Z"
        )
        db.patients[cls.patient_id] = test_patient
        print(f"[SETUP] Using test patient {cls.patient_id} and fundus image {cls.sample_filename}")

    def _get_image_io(self) -> io.BytesIO:
        assert self.sample_image_bytes, "Sample image bytes not loaded"
        return io.BytesIO(self.sample_image_bytes)

    def test_E_model_checkpoint_loading(self):
        """Test E: Verify that models/retinaguard_exp1_best.pth checkpoint loads successfully."""
        self.assertTrue(CHECKPOINT_PATH.exists(), f"Checkpoint missing at {CHECKPOINT_PATH}")
        model = classification_service._load_model()
        self.assertIsNotNone(model)
        self.assertFalse(model.training, "Model must be in eval mode (model.eval())")
        # Ensure cached model is returned on second call (singleton check)
        model2 = classification_service._load_model()
        self.assertIs(model, model2, "Model should be loaded only once and cached as singleton")
        print("[PASS] Test E: Model checkpoint loaded and verified in eval mode (singleton confirmed)")

    def test_A_valid_image_quality_passes_and_classifier_executes(self):
        """Test A: Valid acceptable fundus image passes quality and classifier executes."""
        files = {
            "file": (self.sample_filename, self._get_image_io(), "image/png")
        }
        data = {
            "patient_id": self.patient_id,
            "eye": "OD",
            "screening_center": "Guntur District Hub"
        }
        response = self.client.post("/api/v1/screenings/screen-image", data=data, files=files)
        self.assertEqual(response.status_code, 200, f"Expected 200, got: {response.text}")

        res = response.json()
        self.assertTrue(res["quality"]["passed"], "Quality gate should have passed")
        self.assertIsNotNone(res.get("classification"), "Classification should have executed")
        self.assertIn("grade", res["classification"])
        self.assertIn("confidence", res["classification"])
        print(f"[PASS] Test A: Valid image passed quality and classifier executed -> Grade {res['classification']['grade']}")

    def test_B_poor_quality_image_fails_and_classifier_not_executed(self):
        """Test B: Poor-quality image fails quality gate (HTTP 400) and classifier is NOT executed."""
        # Create heavily blurred image
        nparr = np.frombuffer(self.sample_image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        blurred = cv2.GaussianBlur(img, (61, 61), 25)
        _, blurred_bytes = cv2.imencode(".png", blurred)

        files = {
            "file": ("blurred_fundus.png", io.BytesIO(blurred_bytes.tobytes()), "image/png")
        }
        data = {
            "patient_id": self.patient_id,
            "eye": "OS"
        }
        response = self.client.post("/api/v1/screenings/screen-image", data=data, files=files)
        self.assertEqual(response.status_code, 400, "Quality failure must return HTTP 400")

        res = response.json()
        detail = res.get("detail", {})
        self.assertIn("Quality Gate failed", str(detail))
        if isinstance(detail, dict):
            self.assertIn("quality", detail)
            self.assertFalse(detail["quality"]["passed"])
            self.assertGreater(len(detail["quality"]["issues"]), 0)
            self.assertIn("recapture", detail["quality"]["feedback_text"].lower())

        print("[PASS] Test B: Poor-quality image returned HTTP 400 and classifier was not executed")

    def test_C_valid_image_prediction_structure_and_referral(self):
        """
        Test C: Valid image prediction contains:
        - class / predicted_class
        - dr_label
        - confidence
        - five class probabilities
        - referral status (referable and referral_message)
        """
        files = {
            "file": (self.sample_filename, self._get_image_io(), "image/png")
        }
        data = {
            "patient_id": self.patient_id,
            "eye": "NOT_SPECIFIED"
        }
        response = self.client.post("/api/v1/screenings/screen-image", data=data, files=files)
        self.assertEqual(response.status_code, 200)

        res = response.json()
        classification = res["classification"]

        # Check predicted_class / grade
        self.assertIn("predicted_class", classification)
        self.assertIn("grade", classification)
        pred_class = classification["predicted_class"]
        self.assertIn(pred_class, [0, 1, 2, 3, 4])

        # Check dr_label
        self.assertIn("dr_label", classification)
        expected_labels = ["No DR", "Mild NPDR", "Moderate NPDR", "Severe NPDR", "Proliferative DR"]
        self.assertEqual(classification["dr_label"], expected_labels[pred_class])

        # Check confidence
        self.assertIn("confidence", classification)
        self.assertGreater(classification["confidence"], 0.0)
        self.assertLessEqual(classification["confidence"], 1.0)

        # Check 5 class probabilities
        probs = classification["class_probabilities"]
        self.assertEqual(len(probs), 5)
        for level_key in ["Level 0 (No DR)", "Level 1 (Mild NPDR)", "Level 2 (Moderate NPDR)", "Level 3 (Severe NPDR)", "Level 4 (Proliferative DR)"]:
            self.assertIn(level_key, probs)
            self.assertGreaterEqual(probs[level_key], 0.0)
            self.assertLessEqual(probs[level_key], 1.0)

        # Check referral status
        self.assertIn("referable", classification)
        self.assertEqual(classification["referable"], (pred_class >= 2))
        self.assertIn("referral_message", classification)
        if pred_class >= 2:
            self.assertIn("referral recommended", classification["referral_message"].lower())

        # Top-level screening fields
        self.assertIn("referable", res)
        self.assertEqual(res["referable"], classification["referable"])
        self.assertIn("referral_message", res)

        print(f"[PASS] Test C: Prediction structure verified for Class {pred_class} ({classification['dr_label']}) - Referable: {classification['referable']}")

    def test_D_invalid_corrupted_image_safe_error_response(self):
        """Test D: Invalid or corrupted image data returns safe error response (HTTP 400)."""
        # Upload random garbage bytes as an image
        corrupted_bytes = b"NOT_A_VALID_IMAGE_DATA_CORRUPT_BYTES_XYZ_12345"
        files = {
            "file": ("corrupt.png", io.BytesIO(corrupted_bytes), "image/png")
        }
        data = {
            "patient_id": self.patient_id,
            "eye": "OD"
        }
        response = self.client.post("/api/v1/screenings/screen-image", data=data, files=files)
        self.assertEqual(response.status_code, 400, "Corrupted image must return HTTP 400")
        res = response.json()
        detail_str = str(res.get("detail", ""))
        self.assertTrue(
            "failed" in detail_str.lower() or "invalid" in detail_str.lower() or "unreadable" in detail_str.lower(),
            f"Expected failure message in detail: {detail_str}"
        )
        print(f"[PASS] Test D: Corrupted image handled safely with HTTP 400: {detail_str[:80]}...")


if __name__ == "__main__":
    unittest.main(verbosity=2)
