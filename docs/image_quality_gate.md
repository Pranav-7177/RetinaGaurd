# RetinaGuard Image Quality Gate

## 1. Overview & Clinical Rationale
In automated tele-ophthalmology screening, fundus photograph quality is the primary determinant of diagnostic reliability. Suboptimal images—caused by patient movement, improper illumination, operator misalignment, cataract opacity, or dust on camera optics—lead to diagnostic errors:
- **False Positives**: Optical artifacts or uneven illumination mistaken for hemorrhages or exudates.
- **False Negatives**: Subtle microaneurysms or neovascular vessels obscured by focus blur or underexposure.

The **RetinaGuard Image Quality Gate** runs as an uncompromising triage filter **before** any image enhancement and **before** the final EfficientNet-B0 Diabetic Retinopathy classifier. If an image fails to meet measurable quality criteria, it is immediately rejected with specific recapture guidance, preventing ungradable scans from generating misleading DR grades.

```
Fundus Image ──> Image Quality Gate ──[FAIL]──> Reject & Request Recapture (NO DR Grade)
                          │
                       [PASS]
                          │
                          ▼
                    Preprocessing (CLAHE)
                          │
                          ▼
              Final EfficientNet-B0 Classifier
                          │
                          ▼
                    DR Prediction (Grades 0-4)
```

---

## 2. Why Rule-Based Instead of a Second Trained AI Model?
For the MVP and initial clinical deployments, a deterministic rule-based image-processing approach was chosen over a second deep-learning neural network for the following technical and operational reasons:

1. **Interpretability & Determinism**:
   When an acquisition is rejected in a rural telemedicine clinic, the health worker requires immediate, actionable cause attribution (e.g., *"Focus blurred"* vs. *"Dark illumination"*). Black-box neural networks provide non-specific confidence scores that fail to guide camera adjustments.
2. **Zero Domain Shift / Hallucination Risk**:
   Trained quality models frequently suffer from out-of-distribution hallucinations when deployed across different fundus camera brands (e.g., Topcon vs. Zeiss vs. smartphone ophthalmoscopes). Mathematical pixel statistics (Laplacian variance, intensity distributions, saturation ratios) remain robust across optical setups.
3. **Sub-Second Real-Time Edge Execution**:
   The rule-based pipeline executes in `< 10 milliseconds` on standard CPU hardware without GPU acceleration, providing instant feedback on edge screening tablets before the patient leaves the examination chair.
4. **Independent Fault Isolation**:
   An AI quality model trained on similar data as the DR classifier can share blind spots or systematic biases. A deterministic physical image-processing gate provides true orthogonal verification.

---

## 3. Measurable Metrics & Mathematical Formulations

The quality gate evaluates 5 orthogonal criteria implemented in `backend/services/quality/service.py`:

### a. Retinal Visibility / Field of View (`retinal_visibility_score`)
- **Objective**: Verify that the frame contains a valid retinal disc rather than an empty, blank, or occluded view.
- **Formulation**:
  $$\text{Mask}(x, y) = \mathbb{I}(I_{\text{gray}}(x, y) > 15)$$
  $$R_{\text{vis}} = \frac{\sum_{x, y} \text{Mask}(x, y)}{H \times W}$$
- **Empirical Baseline**: Normal APTOS fundus scans exhibit $0.46 \le R_{\text{vis}} \le 0.91$.
- **Threshold**: $R_{\text{vis}} \ge 0.35$.
- **Score**: $\min\left(1.0, \frac{R_{\text{vis}}}{0.75}\right)$.

### b. Blur & Focus (`blur_score`)
- **Objective**: Detect optical defocus or motion blur.
- **Formulation**: Calculated exclusively on the **green channel** ($G$) inside the retinal bounding box $[y:y+bh, x:x+bw]$ to maximize vascular contrast and eliminate black border edge artifacts:
  $$\sigma_{\text{Lap}}^2 = \text{Var}\left(\nabla^2 G_{\text{retina}}\right) = \frac{1}{N} \sum \left(\nabla^2 G - \mu_{\nabla^2 G}\right)^2$$
- **Empirical Baseline**: Normal APTOS scans range from $4.08$ to $66.22$ (median: $39.44$). Heavily blurred images drop to $< 1.0$.
- **Threshold**: $\sigma_{\text{Lap}}^2 \ge 2.50$.
- **Score**: $\min\left(1.0, 0.5 + 0.5 \times \frac{\sigma_{\text{Lap}}^2}{50.0}\right)$.

### c. Brightness & Illumination (`brightness_score`)
- **Objective**: Prevent underexposed (dark) or overexposed (washed out) acquisitions.
- **Formulation**: Mean intensity of pixels within the retinal foreground mask:
  $$\mu_{\text{retina}} = \frac{1}{|\text{Mask}|} \sum_{(x,y) \in \text{Mask}} I_{\text{gray}}(x, y)$$
- **Empirical Baseline**: Normal APTOS scans range from $42.12$ to $137.69$ (median: $98.62$).
- **Threshold**: $35.0 \le \mu_{\text{retina}} \le 180.0$.
- **Score**:
  - If $\mu \in [35.0, 180.0]$: Normalized distance from ideal center ($100.0$): $\max\left(0.70, 1.0 - \frac{|\mu - 100.0|}{160.0}\right)$.
  - If $\mu < 35.0$: $\frac{\mu}{35.0} \times 0.5$.
  - If $\mu > 180.0$: $\max\left(0.0, 1.0 - \frac{\mu - 180.0}{75.0}\right)$.

### d. Contrast (`contrast_score`)
- **Objective**: Ensure sufficient dynamic range to differentiate retinal lesions from background parenchyma.
- **Formulation**: Standard deviation of retinal intensities:
  $$\sigma_{\text{retina}} = \sqrt{\frac{1}{|\text{Mask}|} \sum_{(x,y) \in \text{Mask}} \left(I_{\text{gray}}(x, y) - \mu_{\text{retina}}\right)^2}$$
- **Empirical Baseline**: Normal APTOS scans range from $10.04$ to $33.48$ (median: $16.93$).
- **Threshold**: $\sigma_{\text{retina}} \ge 8.00$.
- **Score**: $\min\left(1.0, 0.5 + 0.5 \times \frac{\sigma_{\text{retina}}}{35.0}\right)$.

### e. Artifacts & Specular Glare (`artifact_score`)
- **Objective**: Detect specular lens reflections, dust rings, or extreme over-saturation.
- **Formulation**: Ratio of saturated retinal pixels ($I_{\text{gray}} > 248$):
  $$R_{\text{sat}} = \frac{\sum_{(x,y) \in \text{Mask}} \mathbb{I}(I_{\text{gray}}(x, y) > 248)}{|\text{Mask}|}$$
- **Empirical Baseline**: Normal APTOS scans have $R_{\text{sat}} < 0.005$.
- **Threshold**: $R_{\text{sat}} \le 0.15$ (maximum 15% saturated area).
- **Score**: $\min(0.20, R_{\text{sat}} \times 1.33)$ (lower is better).

---

## 4. Pass/Fail Decision Logic & Overall Quality Score

### Overall Quality Score
$$\text{Quality Score} = 0.25 \cdot \text{Blur} + 0.20 \cdot \text{Brightness} + 0.20 \cdot \text{Contrast} + 0.20 \cdot \text{Visibility} + 0.15 \cdot (1.0 - \text{Artifact})$$

### Decision Matrix:
- **`PASS` (`passed = True`)**:
  - All 5 threshold tests must pass ($\text{len}(\text{issues}) == 0$).
  - `state = "GOOD"` if $\text{Quality Score} \ge 0.75$, else `"BORDERLINE"`.
  - `feedback_text`: `"Image quality acceptable. Proceeding to DR screening."`
- **`FAIL` (`passed = False`)**:
  - One or more thresholds violated ($\text{len}(\text{issues}) > 0$).
  - `state = "UNGRADABLE"`.
  - `feedback_text`: `"Image quality insufficient. Please recapture the fundus image."`

---

## 5. Recapture Guidance Messages

| Condition | Failure Trigger | Operator Actionable Guidance |
| :--- | :--- | :--- |
| **Blur / Defocus** | $\sigma_{\text{Lap}}^2 < 2.50$ | `"Image appears blurry. Please ensure camera focus is locked on the retina and recapture."` |
| **Underexposure** | $\mu_{\text{retina}} < 35.0$ | `"Image is too dark. Please improve illumination and recapture."` |
| **Overexposure** | $\mu_{\text{retina}} > 180.0$ | `"Image is overexposed. Please adjust illumination and recapture."` |
| **Low Contrast** | $\sigma_{\text{retina}} < 8.00$ | `"Image has insufficient contrast. Please check lens clarity and lighting balance."` |
| **Occluded / Empty** | $R_{\text{vis}} < 0.35$ | `"Retinal region is not sufficiently visible. Please center the retina in the viewfinder and recapture."` |
| **Specular Glare** | $R_{\text{sat}} > 0.15$ | `"Image contains excessive artifacts or specular glare. Please adjust lens angle to eliminate glare and recapture."` |
| **Invalid Format** | Unreadable bytes | `"Invalid or unreadable image data. Please upload a valid image file (JPG, PNG)."` |
| **Low Resolution** | Dim $< 100 \times 100$ | `"Image resolution too low. Minimum required is 100x100."` |

---

## 6. Integration with DR Classifier & Safety Guarantee

The quality gate is enforced at two architectural levels:

1. **Service Layer (`backend/services/classification/service.py`)**:
   `classify_severity()` verifies the provided `QualityMetrics`. If `passed == False`, it raises a `ValueError` immediately, stopping execution before the model's forward pass.
2. **API Router Layer (`backend/routes/screening.py`)**:
   The `/screenings/{screening_id}/classify-dr` and `/enhance` endpoints check `session.quality`. If the quality check failed, the request is rejected with `HTTP 400 Bad Request` containing the specific failure reasons and recapture instructions.

No DR grade is generated, no confidence is reported, and no misleading results are displayed to the clinician when an image is ungradable.

---

## 7. Known Limitations & Future Enhancements
1. **Severe Cataracts**: Dense cataracts can mimic uniform blur and low contrast. The gate correctly marks these as `UNGRADABLE` for automated screening, prompting manual specialist referral.
2. **Non-Mydriatic Pupil Constriction**: Severe pupil constriction can reduce $R_{\text{vis}}$ below 0.35; the feedback guides the operator to attempt dark-adaptation or pharmacological dilation if permitted.
3. **Future Evolution**: A hybrid architecture where rule-based checks act as a fast first-pass filter, followed by an optional specialized anatomical landmark verification model (optic disc + fovea localization) for edge cases.
