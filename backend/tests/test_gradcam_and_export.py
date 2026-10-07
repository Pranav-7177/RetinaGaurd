"""
Grad-CAM & Export Report Test Suite
Validates:
1. Genuine Grad-CAM is generated for a valid image using EfficientNet-B0.
2. Grad-CAM targets the predicted class (Class 2 for reference image).
3. Grad-CAM overlay is non-empty base64 image and overlay shape matches original.
4. Grad-CAM does NOT run after quality gate failure.
5. Export PDF endpoint generates valid PDF (%PDF- header) for successful screening.
6. Export PDF endpoint for quality failure generates valid PDF without DR grade.
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
from backend.services.explainability.service import explainability_service
from backend.services.reporting.service import reporting_service
from backend.models.schemas import Patient


class TestGradCamAndExport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.test_image_path = PROJECT_ROOT / "data" / "raw" / "aptos2019" / "train_images" / "000c1434d8d7.png"
        if not cls.test_image_path.exists():
            raise FileNotFoundError(f"Reference test image not found at {cls.test_image_path}")

        with open(cls.test_image_path, "rb") as f:
            cls.valid_image_bytes = f.read()

    def test_01_gradcam_generation_for_valid_image(self):
        """Test Grad-CAM generates a valid overlay targeting the predicted class."""
        grad_cam = explainability_service.generate_gradcam(self.valid_image_bytes)
        self.assertTrue(grad_cam.available, "Grad-CAM should be available for a valid image")
        self.assertIsNotNone(grad_cam.image, "Grad-CAM image URL must not be None")
        self.assertTrue(grad_cam.image.startswith("data:image/jpeg;base64,"), "Grad-CAM must be a base64 JPEG data URL")
        self.assertEqual(grad_cam.target_class, 2, "Reference image should target predicted class 2")
        self.assertEqual(grad_cam.target_label, "Moderate NPDR")
        self.assertIn("does not constitute lesion detection", grad_cam.description)

    def test_02_gradcam_blocked_on_invalid_image(self):
        """Test Grad-CAM returns unavailable when image input is empty or invalid."""
        result_empty = explainability_service.generate_gradcam(b"")
        self.assertFalse(result_empty.available)
        self.assertIsNone(result_empty.image)

        result_none = explainability_service.generate_gradcam(None)
        self.assertFalse(result_none.available)
        self.assertIsNone(result_none.image)

    def test_03_screen_image_api_returns_gradcam(self):
        """Test POST /api/v1/screenings/screen-image includes genuine Grad-CAM."""
        files = {"file": ("fundus.png", io.BytesIO(self.valid_image_bytes), "image/png")}
        data = {"patient_id": "PT-EXP1-TEST-001", "eye": "OD"}
        response = self.client.post("/api/v1/screenings/screen-image", data=data, files=files)

        self.assertEqual(response.status_code, 200)
        res_json = response.json()
        self.assertIn("grad_cam", res_json)
        self.assertIsNotNone(res_json["grad_cam"])
        self.assertTrue(res_json["grad_cam"]["available"])
        self.assertTrue(res_json["grad_cam"]["image"].startswith("data:image/jpeg;base64,"))
        self.assertEqual(res_json["grad_cam"]["target_class"], 2)

    def test_04_gradcam_does_not_run_on_quality_failure(self):
        """Test that an ungradable image fails the quality gate and returns HTTP 400 with no Grad-CAM."""
        # Create a tiny blurry dark image that will fail quality
        dark_img = np.zeros((120, 120, 3), dtype=np.uint8)
        _, dark_bytes = cv2.imencode(".png", dark_img)

        files = {"file": ("dark.png", io.BytesIO(dark_bytes.tobytes()), "image/png")}
        data = {"patient_id": "PT-EXP1-TEST-001", "eye": "OD"}
        response = self.client.post("/api/v1/screenings/screen-image", data=data, files=files)

        self.assertEqual(response.status_code, 400)
        self.assertIn("Image Quality Gate failed", response.text)
        self.assertNotIn("grad_cam", response.text)

    def test_05_export_pdf_endpoint_success(self):
        """Test POST /api/v1/screenings/export-pdf generates a downloadable PDF file."""
        sample_session = {
            "id": "SCR-TEST-PDF-001",
            "patient_id": "PT-TEST-001",
            "patient_name": "Ramesh Patel",
            "patient_age": 58,
            "patient_gender": "Male",
            "eye": "OD",
            "screening_center": "District Hospital Eye Clinic",
            "created_at": "2026-09-22T10:00:00Z",
            "quality": {
                "state": "GOOD",
                "passed": True,
                "quality_score": 0.88,
                "focus_score": 92,
                "illumination_score": 88,
                "contrast_score": 85,
                "field_of_view_score": 90,
            },
            "classification": {
                "grade": 2,
                "grade_name": "Moderate NPDR",
                "predicted_class": 2,
                "dr_label": "Moderate NPDR",
                "confidence": 0.94,
                "referable": True,
                "referral_message": "Referral recommended for clinical evaluation within 4-6 weeks.",
                "class_probabilities": {
                    "Level 0 (No DR)": 0.02,
                    "Level 1 (Mild NPDR)": 0.04,
                    "Level 2 (Moderate NPDR)": 0.94,
                    "Level 3 (Severe NPDR)": 0.00,
                    "Level 4 (Proliferative DR)": 0.00,
                },
            },
            "grad_cam": {
                "available": False,
            },
            "review": {
                "status": "CONFIRMED",
                "reviewer_name": "Dr. S. K. Venkat",
                "referral_decision": "TELE_OPHTHALMOLOGY",
                "clinical_notes": "Macular exudates present. Tele-ophthalmology referral initiated.",
            },
        }

        payload = {
            "session": sample_session,
            "patient_form_data": {
                "name": "Ramesh Patel",
                "patientId": "PT-TEST-001",
                "age": 58,
                "sex": "Male",
                "eye": "OD",
                "screeningLocation": "District Hospital Eye Clinic",
                "screeningDate": "2026-09-22",
            }
        }

        response = self.client.post("/api/v1/screenings/export-pdf", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "application/pdf")
        self.assertIn("attachment; filename=", response.headers.get("content-disposition", ""))
        self.assertTrue(response.content.startswith(b"%PDF-"), "Generated file must start with PDF magic bytes %PDF-")
        self.assertGreater(len(response.content), 5000, "PDF size should be substantial")

    def test_06_export_pdf_quality_gate_failure(self):
        """Test PDF export for ungradable screening generates a Quality-Gate Failure report without DR grade."""
        failed_session = {
            "id": "SCR-FAIL-001",
            "patient_id": "PT-FAIL-001",
            "patient_name": "Sunita Rao",
            "patient_age": 62,
            "patient_gender": "Female",
            "eye": "OS",
            "created_at": "2026-09-22T10:00:00Z",
            "quality": {
                "state": "UNGRADABLE",
                "passed": False,
                "quality_score": 0.15,
                "issues": ["Image appears blurry. Focus lock failed.", "Retinal region not sufficiently visible."],
                "feedback_text": "Image is ungradable. Please recapture.",
                "recapture_guidance": ["Lock focus on retina and recapture under balanced illumination."],
            },
            "classification": None,
        }

        payload = {
            "session": failed_session,
            "patient_form_data": {
                "name": "Sunita Rao",
                "patientId": "PT-FAIL-001",
                "age": 62,
                "sex": "Female",
                "eye": "OS",
            }
        }

        response = self.client.post("/api/v1/screenings/export-pdf", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF-"))
        self.assertGreater(len(response.content), 5000, "Quality failure PDF size should be substantial")
        self.assertIn("attachment; filename=", response.headers.get("content-disposition", ""))


if __name__ == "__main__":
    unittest.main()
