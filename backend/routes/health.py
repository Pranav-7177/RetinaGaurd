# pyright: reportMissingImports=false
from fastapi import APIRouter  # type: ignore
from datetime import datetime, timezone
from ..config import settings

router = APIRouter(prefix="/health", tags=["Health & Status"])

@router.get("")
async def get_health():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "model_engine": {
            "status": "initialized",
            "model_version": settings.MODEL_VERSION,
            "architecture": "Hybrid ResNet-VisionTransformer (Scaffold)",
            "device": "CPU / Prototype mode"
        },
        "database": {
            "status": "connected",
            "provider": "InMemory / Supabase Ready"
        },
        "telemedicine_hub": settings.TELEMEDICINE_HUB,
        "disclaimer": settings.DISCLAIMER,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
