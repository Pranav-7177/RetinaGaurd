"""
Diabetic Retinopathy Explainability Service (Grad-CAM)
Computes genuine Grad-CAM attention heatmaps from the trained EfficientNet-B0 model
(models/retinaguard_exp1_best.pth) using PyTorch forward and backward hooks on the
final convolutional layer (features[8]).
"""
import base64
from pathlib import Path
from typing import Union, Optional, Dict, Any
import cv2
import numpy as np
import torch
import torch.nn.functional as F

from ...models.schemas import ExplainabilityData, GradCamResult
from ..classification.service import classification_service, DR_LABELS
from ..quality.service import quality_service
from ...utils.logger import logger


class ExplainabilityService:
    def generate_gradcam(
        self,
        image_input: Union[bytes, str, Path, np.ndarray, None] = None,
        target_class: Optional[int] = None,
    ) -> GradCamResult:
        """
        Generates genuine Grad-CAM explainability overlay from the trained EfficientNet-B0 model.
        
        Requirements:
        1. Loads the existing trained checkpoint (singleton).
        2. Sets model to eval mode.
        3. Preprocesses image matching classification pipeline (224x224, Normalize).
        4. Attaches hooks to the final conv layer: model.features[8] (Conv2dNormActivation).
        5. Computes gradients with respect to target class score.
        6. Global-average pools gradients to compute feature map weights.
        7. Computes weighted activation map with ReLU.
        8. Normalizes and resizes map to original image dimensions.
        9. Creates blended overlay on original fundus image.
        10. Returns GradCamResult with base64 data URL.
        """
        if image_input is None:
            logger.warning("No image provided to generate_gradcam; returning unavailable.")
            return GradCamResult(available=False)

        try:
            # 1. Load image matrix via OpenCV
            img_bgr = quality_service._load_image(image_input)
            if img_bgr is None:
                logger.error("Failed to decode image input for Grad-CAM generation.")
                return GradCamResult(available=False)

            orig_h, orig_w = img_bgr.shape[:2]
            if orig_h < 100 or orig_w < 100:
                logger.warning(f"Image dimensions ({orig_w}x{orig_h}) too small for Grad-CAM.")
                return GradCamResult(available=False)

            # 2. Preprocess image matching model input
            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            tensor = classification_service._transform(img_rgb).unsqueeze(0)

            # 3. Model & Device
            model = classification_service._load_model()
            device = classification_service._get_device()
            tensor = tensor.to(device)

            # 4. PyTorch Hooks on final convolutional layer: model.features[8]
            activations = []
            gradients = []

            def forward_hook(module, inp, out):
                activations.append(out)

            def backward_hook(module, grad_in, grad_out):
                gradients.append(grad_out[0])

            target_layer = model.features[8]
            f_handle = target_layer.register_forward_hook(forward_hook)
            b_handle = target_layer.register_full_backward_hook(backward_hook)

            # 5. Forward and backward passes
            try:
                model.zero_grad()
                outputs = model(tensor)

                if target_class is None:
                    probs = F.softmax(outputs, dim=1).detach().cpu().numpy()[0]
                    target_class = int(np.argmax(probs))

                target_class = int(target_class)
                score = outputs[0, target_class]
                score.backward()
            finally:
                f_handle.remove()
                b_handle.remove()

            if not activations or not gradients:
                logger.error("Failed to capture feature maps or gradients for Grad-CAM.")
                return GradCamResult(available=False)

            # 6. Extract activations and gradients
            act = activations[0].detach()   # Shape: [1, 1280, 7, 7]
            grad = gradients[0].detach()    # Shape: [1, 1280, 7, 7]

            # Global average pooling of gradients across spatial dimensions (H, W)
            weights = torch.mean(grad, dim=(2, 3), keepdim=True)  # [1, 1280, 1, 1]
            cam = torch.sum(weights * act, dim=1, keepdim=True)   # [1, 1, 7, 7]
            cam = F.relu(cam)
            cam = cam.squeeze().cpu().numpy()

            # 7. Normalize activation map safely to [0, 1]
            cam_min = float(cam.min())
            cam_max = float(cam.max())
            if cam_max > cam_min:
                cam_norm = (cam - cam_min) / (cam_max - cam_min + 1e-8)
            else:
                cam_norm = np.zeros_like(cam)

            # 8. Resize activation map to original fundus image dimensions
            cam_resized = cv2.resize(cam_norm, (orig_w, orig_h), interpolation=cv2.INTER_LINEAR)

            # 9. Apply JET colormap and blend overlay
            heatmap_colored = cv2.applyColorMap(np.uint8(255 * cam_resized), cv2.COLORMAP_JET)
            overlay = cv2.addWeighted(img_bgr, 0.65, heatmap_colored, 0.35, 0)

            # 10. Encode overlay image to base64 JPEG
            success, encoded_buf = cv2.imencode(".jpg", overlay, [int(cv2.IMWRITE_JPEG_QUALITY), 88])
            if not success:
                logger.error("Failed to encode Grad-CAM overlay to JPEG.")
                return GradCamResult(available=False)

            b64_str = base64.b64encode(encoded_buf.tobytes()).decode("utf-8")
            data_url = f"data:image/jpeg;base64,{b64_str}"

            label = DR_LABELS.get(target_class, f"Grade {target_class}")
            logger.info(f"Grad-CAM successfully generated for target class {target_class} ({label}).")

            return GradCamResult(
                available=True,
                image=data_url,
                target_class=target_class,
                target_label=label,
                description=(
                    "Grad-CAM highlights image regions that contributed to the model's predicted classification. "
                    "It is an explainability visualization and does not constitute lesion detection or a medical diagnosis."
                ),
            )
        except Exception as exc:
            logger.error(f"Grad-CAM generation failed with exception: {exc}")
            return GradCamResult(available=False)

    def generate_explanation(self, image_data: bytes = None) -> ExplainabilityData:
        """
        Backward-compatible interface returning ExplainabilityData with real Grad-CAM url.
        """
        grad_cam = self.generate_gradcam(image_data)
        return ExplainabilityData(
            gradcam_heatmap_url=grad_cam.image if grad_cam.available else None,
            evidence_rationale=[
                f"Grad-CAM targeted predicted class {grad_cam.target_class} ({grad_cam.target_label})."
                if grad_cam.available
                else "Grad-CAM explainability could not be generated."
            ],
            attention_hotspots=[],
            salient_features=[],
        )


explainability_service = ExplainabilityService()
