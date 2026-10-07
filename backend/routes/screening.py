# pyright: reportMissingImports=false
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Response  # type: ignore
import re
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from ..models.schemas import (
    ScreeningSession, QualityMetrics, RetinalStructure,
    LesionFinding, DRClassification, ExplainabilityData, ClinicalReview,
    GradCamResult, PDFExportRequest
)
from ..models.database import db
from ..services.quality.service import quality_service
from ..services.preprocessing.service import preprocessing_service
from ..services.segmentation.service import segmentation_service
from ..services.lesions.service import lesion_service
from ..services.classification.service import classification_service
from ..services.explainability.service import explainability_service
from ..services.reporting.service import reporting_service
from ..utils.logger import logger

router = APIRouter(prefix="/screenings", tags=["Screening Workspace"])

@router.get("", response_model=List[ScreeningSession])
async def list_screenings(limit: int = 50):
    return list(db.screenings.values())[:limit]

@router.get("/{screening_id}", response_model=ScreeningSession)
async def get_screening(screening_id: str):
    if screening_id not in db.screenings:
        raise HTTPException(status_code=404, detail="Screening session not found")
    return db.screenings[screening_id]

@router.post("/initiate", response_model=ScreeningSession)
async def initiate_screening(
    patient_id: str = Form(...),
    eye: Optional[str] = Form("NOT_SPECIFIED"),
    screening_center: str = Form("District Health Center"),
    file: Optional[UploadFile] = File(None)
):
    patient = db.patients.get(patient_id)
    if not patient:
        # Auto-create lightweight temporary patient if not found
        patient_name = "New Screening Candidate"
        patient_age = 50
        patient_gender = "Other"
    else:
        patient_name = patient.name
        patient_age = patient.age
        patient_gender = patient.gender

    # Normalize eye parameter
    eye_normalized = "NOT_SPECIFIED"
    if eye:
        eye_upper = eye.upper().strip()
        if eye_upper in ["OD", "RIGHT", "RIGHT EYE"]:
            eye_normalized = "OD"
        elif eye_upper in ["OS", "LEFT", "LEFT EYE"]:
            eye_normalized = "OS"
        elif eye_upper in ["NOT_SPECIFIED", "NOT SPECIFIED", "UNKNOWN", "NONE"]:
            eye_normalized = "NOT_SPECIFIED"

    screening_id = f"SCR-2026-{len(db.screenings) + 4401}"
    session = ScreeningSession(
        id=screening_id,
        patient_id=patient_id,
        patient_name=patient_name,
        patient_age=patient_age,
        patient_gender=patient_gender,
        eye=eye_normalized,
        screening_center=screening_center,
        created_at=datetime.now(timezone.utc).isoformat(),
        current_step=1,
        review=ClinicalReview(status="PENDING")
    )

    if file is not None:
        image_bytes = await file.read()
        quality = quality_service.assess_image_quality(image_bytes)
        session.quality = quality
        session.current_step = 3

    db.screenings[screening_id] = session
    return session

@router.post("/screen-image", response_model=ScreeningSession)
async def screen_single_image(
    patient_id: str = Form(...),
    eye: Optional[str] = Form("NOT_SPECIFIED"),
    screening_center: str = Form("District Health Center"),
    file: Optional[UploadFile] = File(None)
):
    """
    Complete single-image screening endpoint:
    Accepts patient ID, one fundus image, and optional eye side (Left Eye, Right Eye, Not Specified).
    Runs: Image -> Quality Gate -> Preprocessing -> Final EfficientNet-B0 -> DR Result.
    If image is omitted or quality fails, blocks classification and returns clear failure guidance (HTTP 400).
    """
    if file is None:
        raise HTTPException(
            status_code=400,
            detail="No fundus image provided. Please upload one fundus image for this screening."
        )

    try:
        image_bytes = await file.read()
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to read uploaded file: {str(exc)}"
        )

    if len(image_bytes) == 0:
        raise HTTPException(
            status_code=400,
            detail="Empty image file received. Please upload a valid fundus photograph."
        )

    # 1. Normalize eye selection
    eye_normalized = "NOT_SPECIFIED"
    if eye:
        eye_upper = eye.upper().strip()
        if eye_upper in ["OD", "RIGHT", "RIGHT EYE"]:
            eye_normalized = "OD"
        elif eye_upper in ["OS", "LEFT", "LEFT EYE"]:
            eye_normalized = "OS"
        elif eye_upper in ["NOT_SPECIFIED", "NOT SPECIFIED", "UNKNOWN", "NONE"]:
            eye_normalized = "NOT_SPECIFIED"

    patient = db.patients.get(patient_id)
    if patient:
        patient_name = patient.name
        patient_age = patient.age
        patient_gender = patient.gender
    else:
        # Do not create a new patient automatically in db.patients
        patient_name = "Candidate"
        patient_age = 50
        patient_gender = "Other"

    screening_id = f"SCR-2026-{len(db.screenings) + 4401}"
    session = ScreeningSession(
        id=screening_id,
        patient_id=patient_id,
        patient_name=patient_name,
        patient_age=patient_age,
        patient_gender=patient_gender,
        eye=eye_normalized,
        screening_center=screening_center,
        created_at=datetime.now(timezone.utc).isoformat(),
        current_step=1,
        review=ClinicalReview(status="PENDING")
    )

    # 2. Image Quality Gate
    quality = quality_service.assess_image_quality(image_bytes)
    session.quality = quality
    session.current_step = 3

    # If quality fails, strictly BLOCK DR classification and return HTTP 400
    if not quality.passed:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Image Quality Gate failed. Image is ungradable and classification is blocked.",
                "quality": {
                    "passed": quality.passed,
                    "quality_score": quality.quality_score,
                    "issues": quality.issues,
                    "feedback_text": quality.feedback_text,
                    "recapture_guidance": quality.recapture_guidance or quality.issues,
                },
                "issues": quality.issues,
                "feedback_text": quality.feedback_text,
            }
        )

    # 3. Preprocessing (CLAHE)
    enhanced_url, meta = preprocessing_service.enhance_fundus(image_bytes)
    session.enhanced_image_url = enhanced_url
    session.current_step = 4

    # 4. Final Model Classification (EfficientNet-B0)
    try:
        classification = classification_service.classify_severity(
            image_input=image_bytes,
            quality_metrics=quality
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=400,
            detail=str(val_err)
        )
    except FileNotFoundError as fnf_err:
        raise HTTPException(
            status_code=500,
            detail=f"Model checkpoint error: {str(fnf_err)}"
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Classification inference failed: {str(exc)}"
        )

    session.classification = classification
    session.referable = classification.referable
    session.referral_message = classification.referral_message

    # 5. Genuine Model Explainability (Grad-CAM)
    try:
        grad_cam = explainability_service.generate_gradcam(
            image_input=image_bytes,
            target_class=classification.grade
        )
        session.grad_cam = grad_cam
        if grad_cam.available:
            session.explainability = ExplainabilityData(
                gradcam_heatmap_url=grad_cam.image,
                evidence_rationale=[
                    f"Grad-CAM targeted predicted class {grad_cam.target_class} ({grad_cam.target_label})."
                ],
                attention_hotspots=[],
                salient_features=[]
            )
    except Exception as exc:
        logger.error(f"Grad-CAM generation error: {exc}")
        session.grad_cam = GradCamResult(available=False)

    session.current_step = 7
    session.is_completed = True

    # Update existing patient record (do not auto-create new patient)
    if patient:
        patient.screenings_count += 1
        patient.last_screening_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        patient.last_dr_grade = classification.grade
        patient.is_referral_active = classification.referable

    db.screenings[screening_id] = session
    return session

@router.post("/{screening_id}/assess-quality", response_model=QualityMetrics)
async def assess_quality(screening_id: str, file: Optional[UploadFile] = File(None)):
    if screening_id not in db.screenings:
        raise HTTPException(status_code=404, detail="Screening session not found")
    
    image_bytes = None
    if file is not None:
        image_bytes = await file.read()
    
    quality = quality_service.assess_image_quality(image_bytes)
    db.screenings[screening_id].quality = quality
    db.screenings[screening_id].current_step = 3
    return quality

@router.post("/{screening_id}/enhance")
async def enhance_image(screening_id: str):
    if screening_id not in db.screenings:
        raise HTTPException(status_code=404, detail="Screening session not found")
    
    session = db.screenings[screening_id]
    if session.quality is not None and not session.quality.passed:
        raise HTTPException(
            status_code=400,
            detail="Cannot enhance image: Image quality assessment failed. Recapture required."
        )
    
    enhanced_url, meta = preprocessing_service.enhance_fundus()
    db.screenings[screening_id].enhanced_image_url = enhanced_url
    db.screenings[screening_id].current_step = 4
    return {"status": "success", "enhanced_image_url": enhanced_url, "metadata": meta}

@router.post("/{screening_id}/analyze-structures", response_model=RetinalStructure)
async def analyze_structures(screening_id: str):
    if screening_id not in db.screenings:
        raise HTTPException(status_code=404, detail="Screening session not found")
    
    structures = segmentation_service.analyze_structures()
    db.screenings[screening_id].retinal_structure = structures
    db.screenings[screening_id].current_step = 5
    return structures

@router.post("/{screening_id}/detect-lesions", response_model=List[LesionFinding])
async def detect_lesions(screening_id: str):
    if screening_id not in db.screenings:
        raise HTTPException(status_code=404, detail="Screening session not found")
    
    lesions = lesion_service.detect_lesions()
    db.screenings[screening_id].lesions = lesions
    db.screenings[screening_id].current_step = 6
    return lesions

@router.post("/{screening_id}/classify-dr", response_model=DRClassification)
async def classify_dr(screening_id: str):
    if screening_id not in db.screenings:
        raise HTTPException(status_code=404, detail="Screening session not found")
    
    session = db.screenings[screening_id]
    if session.quality is not None and not session.quality.passed:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Cannot perform DR classification: Image quality assessment failed. Image is ungradable. Please recapture the fundus image.",
                "quality_state": session.quality.state,
                "issues": session.quality.issues,
                "recapture_guidance": session.quality.recapture_guidance or session.quality.issues,
            }
        )
    
    classification = classification_service.classify_severity(quality_metrics=session.quality)
    db.screenings[screening_id].classification = classification
    db.screenings[screening_id].referable = classification.referable
    db.screenings[screening_id].referral_message = classification.referral_message
    db.screenings[screening_id].current_step = 7
    return classification

@router.post("/{screening_id}/generate-explainability", response_model=ExplainabilityData)
async def generate_explainability(screening_id: str):
    if screening_id not in db.screenings:
        raise HTTPException(status_code=404, detail="Screening session not found")
    
    explainability = explainability_service.generate_explanation()
    db.screenings[screening_id].explainability = explainability
    db.screenings[screening_id].current_step = 8
    return explainability

@router.post("/{screening_id}/submit-review", response_model=ScreeningSession)
async def submit_review(screening_id: str, review: ClinicalReview):
    if screening_id not in db.screenings:
        raise HTTPException(status_code=404, detail="Screening session not found")
    
    review.reviewed_at = datetime.now(timezone.utc).isoformat()
    db.screenings[screening_id].review = review
    db.screenings[screening_id].current_step = 10
    db.screenings[screening_id].is_completed = True
    return db.screenings[screening_id]

@router.get("/{screening_id}/report")
async def get_report(screening_id: str):
    if screening_id not in db.screenings:
        raise HTTPException(status_code=404, detail="Screening session not found")
    
    return reporting_service.generate_screening_report(db.screenings[screening_id])

@router.post("/export-pdf")
async def export_pdf(request: PDFExportRequest):
    """
    Generates and downloads a standardized clinical PDF screening report from the active session result.
    """
    try:
        pdf_bytes = reporting_service.generate_pdf_report(
            session_data=request.session,
            patient_form_data=request.patient_form_data
        )
        patient_id = (
            (request.patient_form_data or {}).get("patientId")
            or request.session.get("patient_id")
            or "Patient"
        )
        safe_pid = re.sub(r'[^a-zA-Z0-9_-]', '_', str(patient_id))
        date_str = datetime.now().strftime("%Y%m%d")
        filename = f"RetinaGuard_Screening_{safe_pid}_{date_str}.pdf"

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except Exception as exc:
        logger.error(f"Failed to generate export PDF: {exc}")
        raise HTTPException(status_code=500, detail=f"Failed to generate export PDF: {str(exc)}")

@router.get("/{screening_id}/export-pdf")
async def export_screening_pdf(screening_id: str):
    """
    Generates and downloads a clinical PDF report for a saved screening session.
    """
    if screening_id not in db.screenings:
        raise HTTPException(status_code=404, detail="Screening session not found")
    
    session = db.screenings[screening_id]
    try:
        pdf_bytes = reporting_service.generate_pdf_report(session)
        safe_pid = re.sub(r'[^a-zA-Z0-9_-]', '_', str(session.patient_id))
        date_str = datetime.now().strftime("%Y%m%d")
        filename = f"RetinaGuard_Screening_{safe_pid}_{date_str}.pdf"

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except Exception as exc:
        logger.error(f"Failed to generate export PDF for session {screening_id}: {exc}")
        raise HTTPException(status_code=500, detail=f"Failed to generate export PDF: {str(exc)}")
