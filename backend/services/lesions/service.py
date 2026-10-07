"""
Lesion Analysis Service Interface
Detects microaneurysms, hard exudates, soft exudates (cotton wool spots), hemorrhages, and neovascularization.
"""
from typing import List
from ...models.schemas import LesionFinding

class LesionAnalysisService:
    def detect_lesions(self, image_data: bytes = None) -> List[LesionFinding]:
        """
        Placeholder interface for object detection / segmentation of retinal lesions.
        """
        return []

lesion_service = LesionAnalysisService()
