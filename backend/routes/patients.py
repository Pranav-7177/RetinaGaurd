# pyright: reportMissingImports=false
from fastapi import APIRouter, HTTPException, Query  # type: ignore
from typing import List, Optional
from datetime import datetime, timezone
from ..models.schemas import Patient, ScreeningSession
from ..models.database import db

router = APIRouter(prefix="/patients", tags=["Patients"])

@router.get("", response_model=List[Patient])
async def list_patients(search: Optional[str] = None):
    patients = list(db.patients.values())
    if search:
        search_lower = search.lower()
        patients = [
            p for p in patients
            if search_lower in p.name.lower() or search_lower in p.id.lower() or search_lower in p.district.lower()
        ]
    return patients

@router.get("/{patient_id}", response_model=Patient)
async def get_patient(patient_id: str):
    if patient_id not in db.patients:
        raise HTTPException(status_code=404, detail="Patient record not found")
    return db.patients[patient_id]

@router.get("/{patient_id}/screenings", response_model=List[ScreeningSession])
async def get_patient_screenings(patient_id: str):
    if patient_id not in db.patients:
        raise HTTPException(status_code=404, detail="Patient record not found")
    
    screenings = [s for s in db.screenings.values() if s.patient_id == patient_id]
    return screenings

@router.post("", response_model=Patient)
async def create_patient(patient: Patient):
    if patient.id in db.patients:
        raise HTTPException(status_code=400, detail="Patient ID already exists")
    patient.registered_at = datetime.now(timezone.utc).isoformat()
    db.patients[patient.id] = patient
    return patient
