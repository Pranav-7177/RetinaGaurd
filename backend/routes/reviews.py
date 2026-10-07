# pyright: reportMissingImports=false
from fastapi import APIRouter, HTTPException, Query  # type: ignore
from typing import List, Optional
from ..models.schemas import ScreeningSession, ClinicalReview
from ..models.database import db

router = APIRouter(prefix="/reviews", tags=["Clinical Review Queue"])

@router.get("/queue", response_model=List[ScreeningSession])
async def get_review_queue(status_filter: Optional[str] = None):
    screenings = list(db.screenings.values())
    if status_filter and status_filter != "ALL":
        screenings = [s for s in screenings if s.review.status == status_filter]
    else:
        # Default show pending first, then confirmed
        screenings.sort(key=lambda s: 0 if s.review.status == "PENDING" else 1)
    return screenings

@router.post("/{screening_id}/adjudicate", response_model=ScreeningSession)
async def adjudicate_review(screening_id: str, review: ClinicalReview):
    if screening_id not in db.screenings:
        raise HTTPException(status_code=404, detail="Screening session not found")
    
    session = db.screenings[screening_id]
    session.review = review
    session.is_completed = True
    return session
