# pyright: reportMissingImports=false
from pydantic import BaseModel, Field  # type: ignore
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime

# Quality Types
QualityState = Literal["GOOD", "BORDERLINE", "UNGRADABLE"]
EyeSide = Literal["OD", "OS", "NOT_SPECIFIED"]  # Right eye (OD), Left eye (OS), or Not Specified
DRGrade = Literal[0, 1, 2, 3, 4]
ReviewStatus = Literal["PENDING", "CONFIRMED", "MODIFIED", "REACQUISITION_REQUESTED"]

class QualityMetrics(BaseModel):
    state: QualityState = "GOOD"
    passed: bool = True
    quality_score: float = Field(default=0.88, ge=0.0, le=1.0)
    overall_score: float = Field(default=0.88, ge=0.0, le=1.0)
    blur_score: float = Field(default=0.91, ge=0.0, le=1.0)
    focus_score: float = Field(default=0.91, ge=0.0, le=1.0)
    brightness_score: float = Field(default=0.85, ge=0.0, le=1.0)
    illumination_score: float = Field(default=0.85, ge=0.0, le=1.0)
    contrast_score: float = Field(default=0.87, ge=0.0, le=1.0)
    retinal_visibility_score: float = Field(default=0.92, ge=0.0, le=1.0)
    field_of_view_score: float = Field(default=0.92, ge=0.0, le=1.0)
    artifact_score: float = Field(default=0.12, ge=0.0, le=1.0)
    issues: List[str] = Field(default_factory=list)
    feedback_text: str = "Image quality acceptable. Proceeding to DR screening."
    enhancement_recommended: bool = False
    recapture_guidance: Optional[List[str]] = None

class RetinalStructure(BaseModel):
    optic_disc_detected: bool = True
    optic_disc_center: List[float] = [0.28, 0.48]  # Normalized [x, y]
    optic_disc_radius: float = 0.08
    fovea_detected: bool = True
    fovea_center: List[float] = [0.55, 0.52]  # Normalized [x, y]
    fovea_radius: float = 0.04
    vessel_density_index: float = 0.74
    arteriovenous_ratio: float = 0.67
    macular_edema_risk: Literal["LOW", "MODERATE", "HIGH"] = "LOW"

class LesionFinding(BaseModel):
    id: str
    lesion_type: Literal["microaneurysm", "hard_exudate", "soft_exudate", "hemorrhage", "neovascularization"]
    confidence: float = Field(ge=0.0, le=1.0)
    bounding_box: List[float]  # [x_min, y_min, x_max, y_max] normalized
    location_quadrant: Literal["superior_nasal", "superior_temporal", "inferior_nasal", "inferior_temporal", "macular"]
    clinical_significance: str

class DRClassification(BaseModel):
    grade: DRGrade = 0
    grade_name: str = "No DR"
    predicted_class: int = 0
    dr_label: str = "No DR"
    referable: bool = False  # Grade >= 2 is referable
    referral_message: str = "Routine screening recommended; no immediate referral required."
    confidence: float = Field(default=0.94, ge=0.0, le=1.0)
    class_probabilities: Dict[str, float] = {
        "Level 0 (No DR)": 0.94,
        "Level 1 (Mild NPDR)": 0.04,
        "Level 2 (Moderate NPDR)": 0.01,
        "Level 3 (Severe NPDR)": 0.005,
        "Level 4 (Proliferative DR)": 0.005,
    }
    key_findings_summary: List[str] = []

class GradCamResult(BaseModel):
    available: bool = False
    image: Optional[str] = None
    target_class: Optional[int] = None
    target_label: Optional[str] = None
    description: str = "Grad-CAM highlights image regions that contributed to the model's predicted classification. It is an explainability visualization and does not constitute lesion detection or a medical diagnosis."

class ExplainabilityData(BaseModel):
    gradcam_heatmap_url: Optional[str] = None
    attention_hotspots: List[Dict[str, Any]] = []
    evidence_rationale: List[str] = []
    salient_features: List[Dict[str, Any]] = []

class ClinicalReview(BaseModel):
    status: ReviewStatus = "PENDING"
    reviewer_id: Optional[str] = None
    reviewer_name: Optional[str] = None
    reviewed_at: Optional[str] = None
    assigned_grade: Optional[DRGrade] = None
    referral_decision: Optional[Literal["NO_REFERRAL", "ROUTINE_MONITORING", "TELE_OPHTHALMOLOGY", "URGENT_TERTIARY"]] = None
    clinical_notes: Optional[str] = None
    reacquisition_reason: Optional[str] = None

class ScreeningSession(BaseModel):
    id: str
    patient_id: str
    patient_name: str
    patient_age: int
    patient_gender: str
    eye: EyeSide = "NOT_SPECIFIED"
    screening_center: str = "District Telemedicine Unit #04"
    created_at: str
    current_step: int = 1
    image_url: Optional[str] = None
    enhanced_image_url: Optional[str] = None
    quality: Optional[QualityMetrics] = None
    retinal_structure: Optional[RetinalStructure] = None
    lesions: List[LesionFinding] = []
    classification: Optional[DRClassification] = None
    explainability: Optional[ExplainabilityData] = None
    grad_cam: Optional[GradCamResult] = None
    review: ClinicalReview = Field(default_factory=ClinicalReview)
    is_completed: bool = False
    model_version: str = "RetinaGuard-Vision-v0.1-proto"
    referable: Optional[bool] = None
    referral_message: Optional[str] = None

class PDFExportRequest(BaseModel):
    session: Dict[str, Any]
    patient_form_data: Optional[Dict[str, Any]] = None

class Patient(BaseModel):
    id: str
    name: str
    age: int
    gender: Literal["Male", "Female", "Other"]
    phone: str
    district: str
    diabetes_type: Literal["Type 1", "Type 2", "Gestational", "Pre-diabetic"]
    diabetes_duration_years: int
    hba1c: Optional[float] = None
    has_hypertension: bool = False
    last_screening_date: Optional[str] = None
    last_dr_grade: Optional[DRGrade] = None
    is_referral_active: bool = False
    screenings_count: int = 0
    registered_at: str

# Simulation Models
class DistrictSimulationInput(BaseModel):
    annual_target_population: int = 25000
    working_days_per_year: int = 260
    screening_centers_count: int = 8
    cameras_per_center: int = 1
    ai_processing_time_seconds: float = 3.5
    ophthalmologists_count: int = 2
    doctor_review_time_minutes: float = 2.0
    telemedicine_bandwidth_mbps: float = 10.0
    referral_triage_rate: float = 0.22  # Percentage of cases requiring review

class DistrictSimulationResult(BaseModel):
    daily_screening_capacity: int
    annual_screening_capacity: int
    ai_utilization_percent: float
    ophthalmologist_utilization_percent: float
    average_review_queue_size: int
    estimated_turnaround_hours: float
    screening_coverage_percent: float
    bottleneck: Literal["Ophthalmologist Review", "Field Cameras", "Bandwidth", "None"]
    recommendations: List[str]
