"""
RetinaGuard Single Fundus Image Screening Test Suite
Validates the MVP workflow requirement: ONE SCREENING = ONE FUNDUS IMAGE.

Test Requirements:
1. One image + Left Eye (OS) succeeds.
2. One image + Right Eye (OD) succeeds.
3. One image + Not Specified (NOT_SPECIFIED) succeeds.
4. One image only (no second eye image required or expected).
5. No image provided returns clear upload rejection message (HTTP 400).
6. Existing patient + new single-eye screening appends new event to patient history.
7. Both eyes screened separately produce two distinct records without combining diagnoses.
"""
import sys
import unittest
from pathlib import Path
import io

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


class TestSingleImageScreeningWorkflow(unittest.TestCase):
    sample_image_bytes: bytes = b""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

        # Locate a valid normal fundus image from APTOS 2019 dataset
        img_dir = PROJECT_ROOT / "data" / "raw" / "aptos2019" / "train_images"
        cls.sample_image_bytes = b""
        for p in img_dir.glob("*.png"):
            with open(p, "rb") as f:
                content = f.read()
                if len(content) > 10000:
                    cls.sample_image_bytes = content
                    cls.sample_filename = p.name
                    break

        if not cls.sample_image_bytes:
            raise FileNotFoundError("Could not find a valid APTOS fundus image for test suite.")

        # Ensure a test patient exists in the database
        cls.test_patient_id = "PT-TEST-MVP-001"
        test_patient = Patient(
            id=cls.test_patient_id,
            name="Aarav Sharma",
            age=54,
            gender="Male",
            phone="+91 98765 43210",
            district="Kolkata",
            diabetes_type="Type 2",
            diabetes_duration_years=8,
            screenings_count=0,
            registered_at="2026-01-15T09:00:00Z"
        )
        db.patients[cls.test_patient_id] = test_patient
        print(f"[SETUP] Prepared test candidate {cls.test_patient_id} with sample image {cls.sample_filename}")

    def _get_image_io(self) -> io.BytesIO:
        assert self.sample_image_bytes, "Sample image bytes not loaded"
        return io.BytesIO(self.sample_image_bytes)

    def test_01_single_image_left_eye_succeeds(self):
        """Test 1: One image + Left Eye (OS) succeeds through the entire pipeline."""
        files = {
            "file": ("fundus_os.png", self._get_image_io(), "image/png")
        }
        data = {
            "patient_id": self.test_patient_id,
            "eye": "OS",
            "screening_center": "Mobile Screening Van"
        }
        response = self.client.post("/api/v1/screenings/screen-image", data=data, files=files)
        self.assertEqual(response.status_code, 200, f"Expected 200 OK, got: {response.text}")

        res = response.json()
        self.assertEqual(res["eye"], "OS")
        self.assertEqual(res["patient_id"], self.test_patient_id)
        self.assertIsNotNone(res.get("quality"))
        self.assertTrue(res["quality"]["passed"])
        self.assertIsNotNone(res.get("classification"))
        self.assertIn("grade", res["classification"])
        self.assertIn(res["classification"]["grade"], [0, 1, 2, 3, 4])
        print(f"[PASS] Test 1: Single image + Left Eye (OS) evaluated successfully -> Grade {res['classification']['grade']}")

    def test_02_single_image_right_eye_succeeds(self):
        """Test 2: One image + Right Eye (OD) succeeds through the entire pipeline."""
        files = {
            "file": ("fundus_od.png", self._get_image_io(), "image/png")
        }
        data = {
            "patient_id": self.test_patient_id,
            "eye": "OD",
            "screening_center": "District Hospital"
        }
        response = self.client.post("/api/v1/screenings/screen-image", data=data, files=files)
        self.assertEqual(response.status_code, 200, f"Expected 200 OK, got: {response.text}")

        res = response.json()
        self.assertEqual(res["eye"], "OD")
        self.assertEqual(res["patient_id"], self.test_patient_id)
        self.assertIsNotNone(res.get("quality"))
        self.assertTrue(res["quality"]["passed"])
        self.assertIsNotNone(res.get("classification"))
        print(f"[PASS] Test 2: Single image + Right Eye (OD) evaluated successfully -> Grade {res['classification']['grade']}")

    def test_03_single_image_not_specified_succeeds(self):
        """Test 3: One image + Not Specified eye succeeds through the entire pipeline."""
        files = {
            "file": ("fundus_unspecified.png", self._get_image_io(), "image/png")
        }
        data = {
            "patient_id": self.test_patient_id,
            "eye": "NOT_SPECIFIED"
        }
        response = self.client.post("/api/v1/screenings/screen-image", data=data, files=files)
        self.assertEqual(response.status_code, 200, f"Expected 200 OK, got: {response.text}")

        res = response.json()
        self.assertEqual(res["eye"], "NOT_SPECIFIED")
        self.assertTrue(res["quality"]["passed"])
        self.assertIsNotNone(res.get("classification"))
        print(f"[PASS] Test 3: Single image + Not Specified eye evaluated successfully -> Eye: {res['eye']}")

    def test_04_single_image_only_no_second_image_required(self):
        """Test 4: Workflow strictly operates on ONE image; no second image or OD/OS pairing required."""
        files = {
            "file": ("single_capture.png", self._get_image_io(), "image/png")
        }
        data = {
            "patient_id": "PT-SOLO-IMAGE",
            "eye": "OS"
        }
        response = self.client.post("/api/v1/screenings/screen-image", data=data, files=files)
        self.assertEqual(response.status_code, 200)
        res = response.json()
        # Session is complete and fully graded with only one image provided
        self.assertTrue(res.get("is_completed"))
        self.assertIsNotNone(res.get("classification"))
        print("[PASS] Test 4: Single image completed screening with no requirement for second image")

    def test_05_no_image_upload_rejected(self):
        """Test 5: Submitting without an image returns HTTP 400 with a clear message."""
        data = {
            "patient_id": self.test_patient_id,
            "eye": "OD"
        }
        # Notice files dict is omitted completely
        response = self.client.post("/api/v1/screenings/screen-image", data=data)
        self.assertEqual(response.status_code, 400)
        res = response.json()
        self.assertIn("No fundus image provided", res["detail"])
        print(f"[PASS] Test 5: Rejection verified when no image provided: '{res['detail']}'")

    def test_06_existing_patient_appends_new_event(self):
        """Test 6: Existing patient + new single-eye screening appends new event to patient record."""
        # Check initial patient screening count
        patient = db.patients[self.test_patient_id]
        initial_count = patient.screenings_count

        files = {
            "file": ("fundus_history.png", self._get_image_io(), "image/png")
        }
        data = {
            "patient_id": self.test_patient_id,
            "eye": "OD"
        }
        response = self.client.post("/api/v1/screenings/screen-image", data=data, files=files)
        self.assertEqual(response.status_code, 200)

        # Confirm count incremented
        self.assertEqual(patient.screenings_count, initial_count + 1)
        print(f"[PASS] Test 6: Patient screening history count incremented from {initial_count} to {patient.screenings_count}")

    def test_07_two_separate_screenings_remain_distinct_events(self):
        """
        Test 7: If a patient has both eyes available, the technician performs TWO SEPARATE SCREENINGS:
        Screening 1 -> Left Eye (OS)
        Screening 2 -> Right Eye (OD)
        Verifies:
        - Two separate screening records/IDs are created.
        - Diagnoses are NOT combined into a single patient-level diagnosis.
        - Each screening retains its own individual eye, quality, and AI staging.
        """
        patient_id = "PT-DUAL-EYE-TEST"
        db.patients[patient_id] = Patient(
            id=patient_id,
            name="Meera Devi",
            age=62,
            gender="Female",
            phone="+91 91234 56789",
            district="Varanasi",
            diabetes_type="Type 2",
            diabetes_duration_years=12,
            screenings_count=0,
            registered_at="2026-02-10T11:00:00Z"
        )

        # Screening 1: Left Eye
        files_os = {
            "file": ("left_eye.png", self._get_image_io(), "image/png")
        }
        data_os = {
            "patient_id": patient_id,
            "eye": "OS",
            "screening_center": "Varanasi Eye Clinic"
        }
        resp_os = self.client.post("/api/v1/screenings/screen-image", data=data_os, files=files_os)
        self.assertEqual(resp_os.status_code, 200)
        session_os = resp_os.json()

        # Screening 2: Right Eye
        files_od = {
            "file": ("right_eye.png", self._get_image_io(), "image/png")
        }
        data_od = {
            "patient_id": patient_id,
            "eye": "OD",
            "screening_center": "Varanasi Eye Clinic"
        }
        resp_od = self.client.post("/api/v1/screenings/screen-image", data=data_od, files=files_od)
        self.assertEqual(resp_od.status_code, 200)
        session_od = resp_od.json()

        # Check that they have distinct session IDs
        self.assertNotEqual(session_os["id"], session_od["id"])
        self.assertEqual(session_os["eye"], "OS")
        self.assertEqual(session_od["eye"], "OD")

        # Query patient's screenings list via API
        history_resp = self.client.get(f"/api/v1/patients/{patient_id}/screenings")
        self.assertEqual(history_resp.status_code, 200)
        history = history_resp.json()

        session_ids = [s["id"] for s in history]
        self.assertIn(session_os["id"], session_ids)
        self.assertIn(session_od["id"], session_ids)
        self.assertEqual(len(session_ids), 2)

        # Verify neither diagnosis was merged or overwritten
        os_record = next(s for s in history if s["id"] == session_os["id"])
        od_record = next(s for s in history if s["id"] == session_od["id"])

        self.assertEqual(os_record["eye"], "OS")
        self.assertEqual(od_record["eye"], "OD")
        self.assertIsNotNone(os_record["classification"])
        self.assertIsNotNone(od_record["classification"])

        print(f"[PASS] Test 7: Both eyes screened as distinct events {os_record['id']} (OS) and {od_record['id']} (OD) without combining diagnoses")


if __name__ == "__main__":
    unittest.main(verbosity=2)
