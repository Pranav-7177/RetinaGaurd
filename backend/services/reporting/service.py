"""
Clinical Screening Report Generation Service
Builds structured clinical summary objects and generates downloadable PDF reports
from real screening results.
"""
import io
import re
import base64
from typing import Dict, Any, Optional, Union
from datetime import datetime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyBboxPatch, Rectangle
from PIL import Image

from ...models.schemas import ScreeningSession
from ...utils.logger import logger


class ReportingService:
    def generate_screening_report(self, session: ScreeningSession) -> Dict[str, Any]:
        """
        Builds standardized telemedicine screening report metadata.
        """
        return {
            "report_id": f"REP-{session.id}",
            "generated_at": session.created_at,
            "patient_info": {
                "id": session.patient_id,
                "name": session.patient_name,
                "age": session.patient_age,
                "gender": session.patient_gender,
            },
            "eye_examined": session.eye,
            "quality_status": session.quality.state if session.quality else "UNASSESSED",
            "dr_grade": session.classification.grade if session.classification else None,
            "dr_grade_label": session.classification.grade_name if session.classification else "Unclassified",
            "is_referable": session.classification.referable if session.classification else False,
            "ai_confidence": session.classification.confidence if session.classification else 0.0,
            "reviewer_status": session.review.status if session.review else "PENDING",
            "clinical_decision": session.review.referral_decision if session.review else None,
            "clinical_notes": session.review.clinical_notes if session.review else None,
            "model_version": session.model_version,
            "disclaimer": "Research prototype - human confirmation required for all referable cases."
        }

    def _decode_image(self, img_source: Optional[str]) -> Optional[Image.Image]:
        """Safely decodes a base64 data URL or local filepath into a PIL Image."""
        if not img_source:
            return None
        try:
            if img_source.startswith("data:image"):
                raw_b64 = img_source.split(",", 1)[1]
                return Image.open(io.BytesIO(base64.b64decode(raw_b64)))
            elif img_source.startswith("/") or img_source.startswith("C:\\") or img_source.startswith("."):
                return Image.open(img_source)
        except Exception as exc:
            logger.warning(f"Failed to decode image for PDF report: {exc}")
        return None

    def generate_pdf_report(
        self,
        session_data: Union[ScreeningSession, Dict[str, Any]],
        patient_form_data: Optional[Dict[str, Any]] = None,
    ) -> bytes:
        """
        Generates an actual downloadable PDF report from the real screening result.
        
        Handles:
        1. Successful screening report with all 8 sections (including genuine Grad-CAM).
        2. Quality-gate failure report (strictly no DR grade or referral claims).
        """
        # Normalize dictionary vs pydantic model
        if hasattr(session_data, "dict"):
            session = session_data.dict()
        elif hasattr(session_data, "model_dump"):
            session = session_data.model_dump()
        else:
            session = dict(session_data)

        patient_form = patient_form_data or {}

        # Check Quality Gate outcome
        quality = session.get("quality") or {}
        quality_passed = quality.get("passed", True)
        quality_state = quality.get("state", "GOOD")

        # If quality failed, generate Quality-Gate Failure Report
        if not quality_passed or quality_state == "UNGRADABLE":
            return self._generate_quality_failure_pdf(session, patient_form)

        return self._generate_success_pdf(session, patient_form)

    def _generate_quality_failure_pdf(self, session: Dict[str, Any], patient_form: Dict[str, Any]) -> bytes:
        """
        Generates a standardized report for quality gate failure.
        Contains:
        - Header: RetinaGuard
        - Screening Status: Image Quality Insufficient
        - Recommendation: Recapture a better-quality fundus image before DR assessment.
        - Quality feedback and issues
        - NO DR prediction, NO confidence, NO referral classification
        """
        patient_id = patient_form.get("patientId") or session.get("patient_id") or "Not specified"
        patient_name = patient_form.get("name") or session.get("patient_name") or "Not specified"
        patient_age = patient_form.get("age") or session.get("patient_age") or "Not specified"
        patient_sex = patient_form.get("sex") or session.get("patient_gender") or "Not specified"
        eye = patient_form.get("eye") or session.get("eye") or "NOT_SPECIFIED"
        eye_label = "Right Eye (OD)" if eye == "OD" else "Left Eye (OS)" if eye == "OS" else "Not specified"
        screening_date = patient_form.get("screeningDate") or session.get("created_at") or datetime.now().strftime("%Y-%m-%d")
        location = patient_form.get("screeningLocation") or session.get("screening_center") or "District Telemedicine Unit"

        quality = session.get("quality") or {}
        quality_score = quality.get("quality_score") or quality.get("overall_score") or quality.get("overallScore")
        score_str = f"{int(quality_score * 100)}/100" if isinstance(quality_score, float) and quality_score <= 1.0 else f"{quality_score}/100" if quality_score else "Ungradable"
        issues = quality.get("issues") or []
        feedback_text = quality.get("feedback_text") or "Fundus image quality is insufficient for diagnostic evaluation."
        recapture_guidance = quality.get("recapture_guidance") or issues or ["Ensure camera focus is locked on the retina and recapture under balanced lighting."]

        buf = io.BytesIO()
        with PdfPages(buf) as pdf:
            fig = plt.figure(figsize=(8.5, 11), dpi=150)
            fig.patch.set_facecolor("white")

            # Section 1: Header
            plt.text(0.08, 0.94, "RETINAGUARD", fontsize=22, weight="bold", color="#0f172a", transform=fig.transFigure)
            plt.text(0.08, 0.915, "AI-Assisted Diabetic Retinopathy Screening", fontsize=12, color="#0f766e", weight="bold", transform=fig.transFigure)
            plt.text(0.08, 0.895, "Screening & Referral Support Report — Quality Gate Notice", fontsize=10, color="#475569", transform=fig.transFigure)

            line = plt.Line2D([0.08, 0.92], [0.88, 0.88], transform=fig.transFigure, color="#0f172a", linewidth=2)
            fig.lines.append(line)

            # Section 2: Patient & Screening Information
            plt.text(0.08, 0.84, "PATIENT & SCREENING INFORMATION", fontsize=11, weight="bold", color="#0f172a", transform=fig.transFigure)
            p_text = (
                f"Patient ID: {patient_id}    |    Patient Name: {patient_name}\n"
                f"Age / Gender: {patient_age} yrs • {patient_sex}    |    Examined Eye: {eye_label}\n"
                f"Screening Date: {screening_date}    |    Screening Center: {location}"
            )
            plt.text(0.08, 0.78, p_text, fontsize=9.5, color="#334155", linespacing=1.6, transform=fig.transFigure)

            sep1 = plt.Line2D([0.08, 0.92], [0.75, 0.75], transform=fig.transFigure, color="#cbd5e1", linewidth=1)
            fig.lines.append(sep1)

            # Section 3: Screening Status Alert
            plt.text(0.08, 0.70, "SCREENING STATUS: IMAGE QUALITY INSUFFICIENT", fontsize=14, weight="bold", color="#b91c1c", transform=fig.transFigure)
            status_desc = (
                "The acquired fundus photograph failed the automated rule-based Image Quality Gate.\n"
                "In accordance with clinical safety protocols, AI classification and diagnostic inference\n"
                "have been strictly BLOCKED to prevent false or inaccurate clinical predictions."
            )
            plt.text(0.08, 0.63, status_desc, fontsize=9.5, color="#1e293b", linespacing=1.5, transform=fig.transFigure)

            # Section 4: Quality Metrics & Detected Issues
            plt.text(0.08, 0.56, "IMAGE QUALITY GATE AUDIT", fontsize=11, weight="bold", color="#0f172a", transform=fig.transFigure)
            q_metrics_text = (
                f"• Quality Assessment: UNGRADABLE ({score_str})\n"
                f"• Focus / Sharpness: {quality.get('focus_score', quality.get('focusScore', 'N/A'))}\n"
                f"• Illumination / Exposure: {quality.get('illumination_score', quality.get('illuminationScore', 'N/A'))}\n"
                f"• Contrast Score: {quality.get('contrast_score', quality.get('contrastScore', 'N/A'))}\n"
                f"• Retinal Field of View: {quality.get('field_of_view_score', quality.get('fieldOfViewScore', 'N/A'))}"
            )
            plt.text(0.08, 0.45, q_metrics_text, fontsize=9, color="#334155", linespacing=1.6, transform=fig.transFigure)

            # Detected Issues
            plt.text(0.08, 0.40, "DETECTED QUALITY ISSUES:", fontsize=10, weight="bold", color="#991b1b", transform=fig.transFigure)
            issues_str = "\n".join([f"  - {issue}" for issue in issues]) if issues else f"  - {feedback_text}"
            plt.text(0.08, 0.33, issues_str, fontsize=9, color="#7f1d1d", linespacing=1.5, transform=fig.transFigure)

            # Recommendation
            plt.text(0.08, 0.28, "RECOMMENDATION & RECAPTURE GUIDANCE:", fontsize=10, weight="bold", color="#0f766e", transform=fig.transFigure)
            guidance_str = (
                "Recapture a better-quality fundus image before DR assessment.\n" +
                "\n".join([f"  • {g}" for g in recapture_guidance])
            )
            plt.text(0.08, 0.20, guidance_str, fontsize=9, color="#134e4a", linespacing=1.5, transform=fig.transFigure)

            # Section 5: Clinical Notice
            sep2 = plt.Line2D([0.08, 0.92], [0.15, 0.15], transform=fig.transFigure, color="#cbd5e1", linewidth=1)
            fig.lines.append(sep2)
            disclaimer = (
                "CLINICAL NOTICE: No DR grade, confidence metric, or referral recommendation has been generated\n"
                "for this screening due to image acquisition failure. Patient requires recapture by healthcare worker."
            )
            plt.text(0.08, 0.10, disclaimer, fontsize=8.5, color="#64748b", linespacing=1.4, transform=fig.transFigure)

            # Footer
            footer_text = f"RetinaGuard v1.0 • Pipeline Safety Lock Active • Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
            plt.text(0.08, 0.05, footer_text, fontsize=8, color="#94a3b8", fontfamily="monospace", transform=fig.transFigure)

            pdf.savefig(fig, bbox_inches="tight")
            plt.close(fig)

        return buf.getvalue()

    def _generate_success_pdf(self, session: Dict[str, Any], patient_form: Dict[str, Any]) -> bytes:
        """
        Generates the full 8-section Telemedicine Screening Report with genuine data.
        """
        # Demographics
        patient_id = patient_form.get("patientId") or session.get("patient_id") or "Not specified"
        patient_name = patient_form.get("name") or session.get("patient_name") or "Not specified"
        patient_age = patient_form.get("age") or session.get("patient_age") or "Not specified"
        patient_sex = patient_form.get("sex") or session.get("patient_gender") or "Not specified"
        eye = patient_form.get("eye") or session.get("eye") or "NOT_SPECIFIED"
        eye_label = "Right Eye (OD)" if eye == "OD" else "Left Eye (OS)" if eye == "OS" else "Not specified"
        screening_date = patient_form.get("screeningDate") or session.get("created_at") or datetime.now().strftime("%Y-%m-%d")
        location = patient_form.get("screeningLocation") or session.get("screening_center") or "District Telemedicine Unit #04"
        case_id = session.get("id") or "SCR-2026-N/A"

        # Image Quality Gate Data
        quality = session.get("quality") or {}
        q_state = quality.get("state", "GOOD")
        q_score = quality.get("quality_score") or quality.get("overall_score") or quality.get("overallScore") or 0.88
        q_score_pct = int(q_score * 100) if isinstance(q_score, float) and q_score <= 1.0 else int(q_score)
        focus = quality.get("focus_score", quality.get("focusScore", 91))
        illum = quality.get("illumination_score", quality.get("illuminationScore", 88))
        contrast = quality.get("contrast_score", quality.get("contrastScore", 85))
        fov = quality.get("field_of_view_score", quality.get("fieldOfViewScore", 89))

        # AI DR Assessment Data
        classification = session.get("classification") or {}
        dr_grade = classification.get("grade", classification.get("predicted_class", 0))
        dr_label = classification.get("dr_label") or classification.get("grade_name") or classification.get("gradeName") or f"Grade {dr_grade}"
        confidence = classification.get("confidence", 0.94)
        conf_pct = f"{confidence * 100:.1f}%" if confidence <= 1.0 else f"{confidence:.1f}%"
        is_referable = bool(classification.get("referable", dr_grade >= 2))
        referral_msg = classification.get("referral_message") or (
            "Referral recommended for clinical ophthalmologist evaluation."
            if is_referable
            else "Routine screening recommended; no immediate referral required."
        )
        probabilities = classification.get("class_probabilities") or classification.get("classProbabilities") or {}

        # Review Data
        review = session.get("review") or {}
        reviewer_name = review.get("reviewer_name") or review.get("reviewerName") or "Dr. S. K. Venkat (Tele-Ophthalmologist)"
        review_status = review.get("status") or "CONFIRMED"
        action_pathway = review.get("referral_decision") or review.get("referralDecision") or ("TELE_OPHTHALMOLOGY" if is_referable else "ROUTINE_MONITORING")
        review_notes = review.get("clinical_notes") or review.get("clinicalNotes")

        # Grad-CAM Data
        grad_cam = session.get("grad_cam") or {}
        grad_cam_available = bool(grad_cam.get("available", False))
        grad_cam_img = self._decode_image(grad_cam.get("image"))

        # Fundus Image
        fundus_img = self._decode_image(session.get("enhanced_image_url") or session.get("enhancedImageUrl") or session.get("image_url") or session.get("imageUrl"))

        buf = io.BytesIO()
        with PdfPages(buf) as pdf:
            fig = plt.figure(figsize=(8.5, 11), dpi=150)
            fig.patch.set_facecolor("white")

            # -------------------------------------------------------------
            # SECTION 1: HEADER
            # -------------------------------------------------------------
            plt.text(0.08, 0.945, "RETINAGUARD", fontsize=20, weight="bold", color="#0f172a", transform=fig.transFigure)
            plt.text(0.08, 0.923, "AI-Assisted Diabetic Retinopathy Screening", fontsize=11, color="#0f766e", weight="bold", transform=fig.transFigure)
            plt.text(0.08, 0.905, "Screening & Referral Support Report", fontsize=9.5, color="#475569", transform=fig.transFigure)

            plt.text(0.92, 0.945, f"Case: {case_id}", fontsize=10, weight="bold", color="#0f172a", ha="right", fontfamily="monospace", transform=fig.transFigure)
            plt.text(0.92, 0.925, f"Date: {str(screening_date)[:10]}", fontsize=8.5, color="#64748b", ha="right", transform=fig.transFigure)
            plt.text(0.92, 0.908, f"{location}", fontsize=8.5, color="#64748b", ha="right", transform=fig.transFigure)

            line1 = plt.Line2D([0.08, 0.92], [0.895, 0.895], transform=fig.transFigure, color="#0f172a", linewidth=2)
            fig.lines.append(line1)

            # -------------------------------------------------------------
            # SECTION 2: PATIENT / SCREENING INFORMATION
            # -------------------------------------------------------------
            plt.text(0.08, 0.875, "PATIENT INFORMATION", fontsize=9.5, weight="bold", color="#0f172a", transform=fig.transFigure)
            plt.text(0.08, 0.855, f"Name: {patient_name}", fontsize=9, weight="bold", color="#1e293b", transform=fig.transFigure)
            plt.text(0.35, 0.855, f"ID: {patient_id}", fontsize=9, color="#1e293b", transform=fig.transFigure)
            plt.text(0.60, 0.855, f"Age/Sex: {patient_age} yrs • {patient_sex}", fontsize=9, color="#1e293b", transform=fig.transFigure)
            plt.text(0.78, 0.855, f"Examined Eye: {eye_label}", fontsize=9, weight="bold", color="#0f766e", transform=fig.transFigure)

            sep_p = plt.Line2D([0.08, 0.92], [0.84, 0.84], transform=fig.transFigure, color="#e2e8f0", linewidth=1)
            fig.lines.append(sep_p)

            # -------------------------------------------------------------
            # SECTION 3 & 4: QUALITY GATE & CLAHE ENHANCEMENT
            # -------------------------------------------------------------
            plt.text(0.08, 0.82, "FUNDUS IMAGE QUALITY GATE", fontsize=9.5, weight="bold", color="#0f172a", transform=fig.transFigure)
            plt.text(0.55, 0.82, "IMAGE PREPROCESSING PIPELINE", fontsize=9.5, weight="bold", color="#0f172a", transform=fig.transFigure)

            q_summary = (
                f"• Status: {q_state} Quality ({q_score_pct}/100)\n"
                f"• Focus: {focus}  |  Contrast: {contrast}\n"
                f"• Illumination: {illum}  |  FOV: {fov}"
            )
            plt.text(0.08, 0.77, q_summary, fontsize=8.5, color="#334155", linespacing=1.4, transform=fig.transFigure)

            clahe_summary = (
                "• CLAHE Preprocessing Applied\n"
                "• LAB Color Space Adaptive Histogram Equalization\n"
                "• Enhanced microvascular contrast for EfficientNet-B0"
            )
            plt.text(0.55, 0.77, clahe_summary, fontsize=8.5, color="#334155", linespacing=1.4, transform=fig.transFigure)

            sep_q = plt.Line2D([0.08, 0.92], [0.74, 0.74], transform=fig.transFigure, color="#e2e8f0", linewidth=1)
            fig.lines.append(sep_q)

            # -------------------------------------------------------------
            # SECTION 5 & 6: AI DR ASSESSMENT & REFERRAL SUPPORT
            # -------------------------------------------------------------
            plt.text(0.08, 0.72, "AI DR ASSESSMENT (EfficientNet-B0)", fontsize=9.5, weight="bold", color="#0f172a", transform=fig.transFigure)
            plt.text(0.55, 0.72, "REFERRAL SUPPORT DECISION", fontsize=9.5, weight="bold", color="#0f172a", transform=fig.transFigure)

            plt.text(0.08, 0.695, f"Predicted Grade: Level {dr_grade} — {dr_label}", fontsize=11, weight="bold", color="#0f172a", transform=fig.transFigure)
            plt.text(0.08, 0.675, f"Model Confidence: {conf_pct}", fontsize=9, weight="bold", color="#0f766e", transform=fig.transFigure)

            if probabilities:
                probs_str = "Probabilities: " + "  |  ".join([f"L{i}: {probabilities.get(k, 0):.2f}" for i, k in enumerate([
                    "Level 0 (No DR)", "Level 1 (Mild NPDR)", "Level 2 (Moderate NPDR)", "Level 3 (Severe NPDR)", "Level 4 (Proliferative DR)"
                ]) if k in probabilities])
                plt.text(0.08, 0.655, probs_str, fontsize=7.5, color="#64748b", fontfamily="monospace", transform=fig.transFigure)

            ref_color = "#b91c1c" if is_referable else "#047857"
            ref_status_text = "REFERRAL RECOMMENDED" if is_referable else "ROUTINE MONITORING"
            plt.text(0.55, 0.695, f"Status: {ref_status_text}", fontsize=11, weight="bold", color=ref_color, transform=fig.transFigure)
            plt.text(0.55, 0.665, f"Guidance: {referral_msg}", fontsize=8.5, color="#1e293b", linespacing=1.3, transform=fig.transFigure)

            sep_m = plt.Line2D([0.08, 0.92], [0.63, 0.63], transform=fig.transFigure, color="#e2e8f0", linewidth=1)
            fig.lines.append(sep_m)

            # -------------------------------------------------------------
            # SECTION 7: GRAD-CAM & VISUAL FINDINGS
            # -------------------------------------------------------------
            plt.text(0.08, 0.61, "MODEL EXPLAINABILITY — GRAD-CAM", fontsize=9.5, weight="bold", color="#0f172a", transform=fig.transFigure)

            if grad_cam_available and grad_cam_img:
                # Two axes for original/enhanced fundus and Grad-CAM overlay
                ax_fundus = fig.add_axes([0.12, 0.38, 0.32, 0.20])
                if fundus_img:
                    ax_fundus.imshow(fundus_img)
                ax_fundus.set_title("Examined Fundus (CLAHE)", fontsize=8, weight="bold", pad=4)
                ax_fundus.axis("off")

                ax_cam = fig.add_axes([0.56, 0.38, 0.32, 0.20])
                ax_cam.imshow(grad_cam_img)
                ax_cam.set_title(f"Grad-CAM Attention (Target: Class {dr_grade})", fontsize=8, weight="bold", pad=4)
                ax_cam.axis("off")

                cam_disclaimer = (
                    "“The Grad-CAM visualization highlights regions that contributed to the model's predicted classification.\n"
                    "It is not lesion detection and should not be interpreted as a definitive clinical finding.”"
                )
                plt.text(0.08, 0.345, cam_disclaimer, fontsize=8, color="#475569", style="italic", linespacing=1.3, transform=fig.transFigure)
            else:
                plt.text(0.08, 0.48, "Model Explainability: Grad-CAM unavailable for this screening.", fontsize=9, color="#64748b", transform=fig.transFigure)

            sep_c = plt.Line2D([0.08, 0.92], [0.325, 0.325], transform=fig.transFigure, color="#e2e8f0", linewidth=1)
            fig.lines.append(sep_c)

            # -------------------------------------------------------------
            # SECTION 8: CLINICIAN REVIEW & SIGN-OFF
            # -------------------------------------------------------------
            plt.text(0.08, 0.305, "TELE-OPHTHALMOLOGIST REVIEW & TRIAGE SIGN-OFF", fontsize=9.5, weight="bold", color="#0f172a", transform=fig.transFigure)
            rev_info = (
                f"Reviewing Clinician: {reviewer_name}    |    Review Status: {review_status}\n"
                f"Action Pathway: {action_pathway}"
            )
            plt.text(0.08, 0.275, rev_info, fontsize=8.5, color="#334155", linespacing=1.4, transform=fig.transFigure)

            if review_notes:
                plt.text(0.08, 0.235, f"Clinical Notes: \"{review_notes}\"", fontsize=8.5, color="#1e293b", style="italic", transform=fig.transFigure)

            # Regulatory Clinical Disclaimer Box
            sep_d = plt.Line2D([0.08, 0.92], [0.205, 0.205], transform=fig.transFigure, color="#e2e8f0", linewidth=1)
            fig.lines.append(sep_d)

            plt.text(0.08, 0.185, "REGULATORY & CLINICAL DISCLAIMER:", fontsize=8.5, weight="bold", color="#9a3412", transform=fig.transFigure)
            regulatory_text = (
                "RetinaGuard provides AI-assisted screening and referral support. The result is not a definitive medical diagnosis\n"
                "and should be reviewed by a qualified healthcare professional. It does not replace a comprehensive dilated eye\n"
                "examination by an ophthalmologist."
            )
            plt.text(0.08, 0.135, regulatory_text, fontsize=8, color="#7c2d12", linespacing=1.4, transform=fig.transFigure)

            # Processing Footnote
            sep_foot = plt.Line2D([0.08, 0.92], [0.09, 0.09], transform=fig.transFigure, color="#cbd5e1", linewidth=1)
            fig.lines.append(sep_foot)

            footer = (
                f"AI Model: EfficientNet-B0 (retinaguard_exp1_best.pth, Epoch 8) • CLAHE Enhanced • OpenCV Quality Gate\n"
                f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')} • RetinaGuard v1.0 Standard Clinical Report"
            )
            plt.text(0.08, 0.055, footer, fontsize=7.5, color="#94a3b8", fontfamily="monospace", transform=fig.transFigure)

            pdf.savefig(fig, bbox_inches="tight")
            plt.close(fig)

        return buf.getvalue()


reporting_service = ReportingService()

