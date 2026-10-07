from typing import Dict, List, Optional
from datetime import datetime, timedelta
from .schemas import (
    Patient, ScreeningSession, QualityMetrics, RetinalStructure,
    LesionFinding, DRClassification, ExplainabilityData, ClinicalReview
)

class InMemoryDatabase:
    def __init__(self):
        self.patients: Dict[str, Patient] = {}
        self.screenings: Dict[str, ScreeningSession] = {}
        self.seed_data()

    def seed_data(self):
        # Sample patients
        p1 = Patient(
            id="PT-2026-0891",
            name="Rameshwar Prasad",
            age=58,
            gender="Male",
            phone="+91 98451 22910",
            district="Kurnool Rural Sub-District",
            diabetes_type="Type 2",
            diabetes_duration_years=12,
            hba1c=8.4,
            has_hypertension=True,
            last_screening_date="2026-09-18",
            last_dr_grade=2,
            is_referral_active=True,
            screenings_count=2,
            registered_at="2025-10-14"
        )
        p2 = Patient(
            id="PT-2026-0892",
            name="Lakshmi Devi",
            age=52,
            gender="Female",
            phone="+91 97312 88419",
            district="Anantapur North",
            diabetes_type="Type 2",
            diabetes_duration_years=6,
            hba1c=6.9,
            has_hypertension=False,
            last_screening_date="2026-09-19",
            last_dr_grade=0,
            is_referral_active=False,
            screenings_count=1,
            registered_at="2026-01-20"
        )
        p3 = Patient(
            id="PT-2026-0893",
            name="Abdul Kareem",
            age=64,
            gender="Male",
            phone="+91 94480 33182",
            district="Kadapa South Primary Health Center",
            diabetes_type="Type 2",
            diabetes_duration_years=18,
            hba1c=9.8,
            has_hypertension=True,
            last_screening_date="2026-09-19",
            last_dr_grade=3,
            is_referral_active=True,
            screenings_count=4,
            registered_at="2024-06-11"
        )
        p4 = Patient(
            id="PT-2026-0894",
            name="Sunita Bai",
            age=46,
            gender="Female",
            phone="+91 91234 56789",
            district="Chittoor West Camp",
            diabetes_type="Type 1",
            diabetes_duration_years=15,
            hba1c=7.5,
            has_hypertension=False,
            last_screening_date="2026-09-17",
            last_dr_grade=1,
            is_referral_active=False,
            screenings_count=3,
            registered_at="2025-03-02"
        )
        p5 = Patient(
            id="PT-2026-0895",
            name="Mohan Rao",
            age=69,
            gender="Male",
            phone="+91 98860 11234",
            district="Nellore Tribal Outreach",
            diabetes_type="Type 2",
            diabetes_duration_years=22,
            hba1c=10.2,
            has_hypertension=True,
            last_screening_date="2026-09-19",
            last_dr_grade=4,
            is_referral_active=True,
            screenings_count=5,
            registered_at="2023-11-19"
        )

        for p in [p1, p2, p3, p4, p5]:
            self.patients[p.id] = p

        # Sample screenings
        s1 = ScreeningSession(
            id="SCR-2026-4401",
            patient_id="PT-2026-0891",
            patient_name="Rameshwar Prasad",
            patient_age=58,
            patient_gender="Male",
            eye="OD",
            screening_center="Kurnool Rural Sub-District Health Center",
            created_at="2026-09-18T10:30:00",
            current_step=7,
            image_url="/assets/samples/sample_dr2_fundus.jpg",
            quality=QualityMetrics(
                state="GOOD",
                overall_score=0.92,
                focus_score=0.94,
                illumination_score=0.89,
                contrast_score=0.91,
                field_of_view_score=0.95,
                artifact_score=0.08
            ),
            retinal_structure=None,
            lesions=[],
            classification=DRClassification(
                grade=2,
                grade_name="Moderate Non-Proliferative Diabetic Retinopathy (NPDR)",
                referable=True,
                confidence=0.89,
                class_probabilities={
                    "Level 0 (No DR)": 0.02,
                    "Level 1 (Mild NPDR)": 0.09,
                    "Level 2 (Moderate NPDR)": 0.89,
                    "Level 3 (Severe NPDR)": 0.05,
                    "Level 4 (Proliferative DR)": 0.00,
                },
                key_findings_summary=[
                    "Multiple microaneurysms in temporal arcade",
                    "Hard exudates present within 1 disc diameter of fovea",
                    "Moderate intraretinal dot hemorrhages"
                ]
            ),
            explainability=None,
            review=ClinicalReview(
                status="PENDING",
                reviewer_name="Dr. S. K. Venkat (Ophthalmologist)",
                assigned_grade=2,
                referral_decision="TELE_OPHTHALMOLOGY",
                clinical_notes="Awaiting tele-consult confirmation. Advise OCT macular scan at district hospital."
            ),
            is_completed=True
        )

        s2 = ScreeningSession(
            id="SCR-2026-4402",
            patient_id="PT-2026-0892",
            patient_name="Lakshmi Devi",
            patient_age=52,
            patient_gender="Female",
            eye="OS",
            screening_center="Anantapur North PHC",
            created_at="2026-09-19T09:15:00",
            current_step=7,
            image_url="/assets/samples/sample_normal_fundus.jpg",
            quality=QualityMetrics(
                state="GOOD",
                overall_score=0.96,
                focus_score=0.97,
                illumination_score=0.95,
                contrast_score=0.96,
                field_of_view_score=0.98,
                artifact_score=0.03
            ),
            retinal_structure=None,
            lesions=[],
            classification=DRClassification(
                grade=0,
                grade_name="No Apparent Diabetic Retinopathy",
                referable=False,
                confidence=0.97,
                class_probabilities={
                    "Level 0 (No DR)": 0.97,
                    "Level 1 (Mild NPDR)": 0.02,
                    "Level 2 (Moderate NPDR)": 0.01,
                    "Level 3 (Severe NPDR)": 0.00,
                    "Level 4 (Proliferative DR)": 0.00,
                },
                key_findings_summary=[
                    "Clear optic disc margins with normal cup-to-disc ratio (0.3).",
                    "Uniform retinal background with no microaneurysms or exudates."
                ]
            ),
            explainability=None,
            review=ClinicalReview(
                status="CONFIRMED",
                reviewer_id="DOC-81",
                reviewer_name="Dr. Anita Sharma",
                reviewed_at="2026-09-19T10:00:00",
                assigned_grade=0,
                referral_decision="ROUTINE_MONITORING",
                clinical_notes="Clear fundus. Repeat annual community screening in 12 months."
            ),
            is_completed=True
        )

        s3 = ScreeningSession(
            id="SCR-2026-4403",
            patient_id="PT-2026-0893",
            patient_name="Abdul Kareem",
            patient_age=64,
            patient_gender="Male",
            eye="OD",
            screening_center="Kadapa South PHC",
            created_at="2026-09-19T11:45:00",
            current_step=7,
            image_url="/assets/samples/sample_dr3_fundus.jpg",
            quality=QualityMetrics(
                state="GOOD",
                overall_score=0.88,
                focus_score=0.89,
                illumination_score=0.86,
                contrast_score=0.88,
                field_of_view_score=0.92,
                artifact_score=0.10
            ),
            retinal_structure=None,
            lesions=[],
            classification=DRClassification(
                grade=3,
                grade_name="Severe Non-Proliferative Diabetic Retinopathy (NPDR)",
                referable=True,
                confidence=0.92,
                class_probabilities={
                    "Level 0 (No DR)": 0.00,
                    "Level 1 (Mild NPDR)": 0.01,
                    "Level 2 (Moderate NPDR)": 0.07,
                    "Level 3 (Severe NPDR)": 0.92,
                    "Level 4 (Proliferative DR)": 0.00,
                },
                key_findings_summary=[
                    "Severe intraretinal hemorrhages meeting 4-2-1 international clinical staging.",
                    "Cotton wool spots (soft exudates) in superior temporal quadrant.",
                    "Venous caliber irregularities noted."
                ]
            ),
            explainability=None,
            review=ClinicalReview(
                status="PENDING",
                reviewer_name=None,
                assigned_grade=3,
                referral_decision="URGENT_TERTIARY",
                clinical_notes="High risk of conversion to proliferative disease. Priority ophthalmology appointment required."
            ),
            is_completed=True
        )

        for s in [s1, s2, s3]:
            self.screenings[s.id] = s

db = InMemoryDatabase()
