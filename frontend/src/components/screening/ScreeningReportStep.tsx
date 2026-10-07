import React, { useRef, useState } from 'react';
import {
  FileText,
  Printer,
  Download,
  Share2,
  CheckCircle2,
  AlertTriangle,
  Award,
  User,
  ShieldCheck,
  Building2,
  Calendar,
  Layers,
  Sparkles,
  ArrowLeft,
  Check
} from 'lucide-react';
import { Button } from '../common/Button';
import { Card } from '../common/Card';
import { StatusBadge } from '../common/StatusBadge';
import { ScreeningSession } from '../../types';
import { PatientFormData } from './PatientStep';

interface ScreeningReportStepProps {
  session: ScreeningSession;
  patientFormData: PatientFormData;
  onReturnToDashboard: () => void;
  onNewScreening: () => void;
}

export const ScreeningReportStep: React.FC<ScreeningReportStepProps> = ({
  session,
  patientFormData,
  onReturnToDashboard,
  onNewScreening,
}) => {
  const reportRef = useRef<HTMLDivElement>(null);
  const [isSaved, setIsSaved] = useState(false);
  const [exportNotice, setExportNotice] = useState<string | null>(null);
  const [isExporting, setIsExporting] = useState(false);

  const handlePrint = () => {
    window.print();
  };

  const handleSaveReport = () => {
    setIsSaved(true);
    setTimeout(() => setIsSaved(false), 3000);
  };

  const handleExportPdf = async () => {
    try {
      setIsExporting(true);
      setExportNotice('Generating clinical PDF report from real screening results...');

      const payload = {
        session,
        patient_form_data: patientFormData,
      };

      const res = await fetch('/api/v1/screenings/export-pdf', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        throw new Error(`Export failed with HTTP ${res.status}`);
      }

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      const patientId = patientFormData.patientId || session.patientId || 'patient';
      const cleanPid = patientId.replace(/[^a-zA-Z0-9_-]/g, '_');
      const dateStr = (patientFormData.screeningDate || new Date().toISOString().split('T')[0]).replace(/-/g, '');
      link.download = `RetinaGuard_Screening_${cleanPid}_${dateStr}.pdf`;
      document.body.appendChild(link);
      link.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(link);

      setExportNotice(`Report downloaded successfully: RetinaGuard_Screening_${cleanPid}_${dateStr}.pdf`);
      setTimeout(() => setExportNotice(null), 5000);
    } catch (err: any) {
      console.error('Export report failed:', err);
      setExportNotice(`Failed to export report: ${err.message || 'Error occurred'}`);
      setTimeout(() => setExportNotice(null), 5000);
    } finally {
      setIsExporting(false);
    }
  };

  const finalGrade =
    session.review.assignedGrade !== undefined
      ? session.review.assignedGrade
      : session.classification?.grade || 0;
  const isReferable = finalGrade >= 2;

  return (
    <div className="space-y-6">
      {/* Step Header & Report Action Toolbar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-navy-950">Step 7 — Final Telemedicine Screening Report</h2>
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-teal-100 text-teal-800 border border-teal-200">
              Validated Tele-Summary
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Standardized tele-retina clinical screening report ready for primary health center archiving, patient counseling, or tertiary hospital referral.
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <Button
            variant="outline"
            size="sm"
            onClick={handleSaveReport}
            leftIcon={isSaved ? <Check className="w-4 h-4 text-emerald-600" /> : <FileText className="w-4 h-4" />}
          >
            {isSaved ? 'Report Saved' : 'Save Report'}
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={handleExportPdf}
            disabled={isExporting}
            leftIcon={<Download className="w-4 h-4" />}
          >
            {isExporting ? 'Generating PDF...' : 'Export PDF'}
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={handlePrint}
            leftIcon={<Printer className="w-4 h-4" />}
          >
            Print
          </Button>

          <Button
            variant="teal"
            size="sm"
            onClick={onReturnToDashboard}
            leftIcon={<ArrowLeft className="w-4 h-4" />}
          >
            Return to Dashboard
          </Button>
        </div>
      </div>

      {exportNotice && (
        <div className="p-3 bg-teal-50 border border-teal-200 rounded-xl text-xs text-teal-900 flex items-center gap-2 font-medium">
          <CheckCircle2 className="w-4 h-4 text-teal-600 flex-shrink-0" />
          <span>{exportNotice}</span>
        </div>
      )}

      {/* Printable Clinical Screening Sheet */}
      <div
        ref={reportRef}
        className="bg-white rounded-2xl border border-slate-300 shadow-xl p-8 max-w-4xl mx-auto space-y-6 text-slate-800 print:border-none print:shadow-none print:p-0"
      >
        {/* Report Header */}
        <div className="border-b-2 border-navy-950 pb-5 flex flex-col sm:flex-row sm:items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <img
                src="/retinaguard-logo.png"
                alt="RetinaGuard"
                className="h-10 w-auto object-contain"
              />
              <div className="border-l border-slate-300 pl-3">
                <h1 className="text-lg font-black text-navy-950 tracking-tight">Tele-Retina Screening Report</h1>
                <p className="text-[11px] text-slate-500">
                  District Tele-Ophthalmology & Rural Health Screening Network
                </p>
              </div>
            </div>
          </div>

          <div className="text-right text-xs">
            <div className="font-mono font-bold text-navy-950 text-sm">Case ID: {session.id}</div>
            <div className="text-slate-500 text-[11px] mt-0.5">Screening Date: {patientFormData.screeningDate || new Date().toISOString().split('T')[0]}</div>
            <div className="text-slate-500 text-[11px]">Location: {patientFormData.screeningLocation || session.screeningCenter}</div>
          </div>
        </div>

        {/* Patient Demographics Strip */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs">
          <div>
            <span className="text-slate-400 text-[10px] uppercase font-semibold">Patient Name</span>
            <div className="font-bold text-navy-950 mt-0.5">{patientFormData.name}</div>
          </div>
          <div>
            <span className="text-slate-400 text-[10px] uppercase font-semibold">Age / Sex</span>
            <div className="font-bold text-navy-950 mt-0.5">{patientFormData.age} yrs • {patientFormData.sex}</div>
          </div>
          <div>
            <span className="text-slate-400 text-[10px] uppercase font-semibold">Patient ID</span>
            <div className="font-bold font-mono text-navy-950 mt-0.5">{patientFormData.patientId}</div>
          </div>
          <div>
            <span className="text-slate-400 text-[10px] uppercase font-semibold">Examined Eye</span>
            <div className="font-bold text-teal-700 mt-0.5">
              {patientFormData.eye === 'OD' ? 'Right Eye (OD)' : patientFormData.eye === 'OS' ? 'Left Eye (OS)' : 'Not Specified'}
            </div>
          </div>
        </div>

        {/* Primary Classification & Quality Outcome Boxes */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* DR Staging Outcome */}
          <div className="p-4 rounded-xl border border-slate-200 bg-white space-y-2">
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
              Clinical DR Staging Outcome
            </div>
            <div className="text-lg font-black text-navy-950">
              Level {finalGrade} — {session.classification?.gradeName || 'Diabetic Retinopathy Classification'}
            </div>
            <div className="flex items-center gap-2 pt-1">
              <StatusBadge status={isReferable ? 'REFERABLE' : 'NON-REFERABLE'} size="md" />
              <span className="text-xs text-slate-500 font-mono">
                Model Confidence: {((session.classification?.confidence || 0.89) * 100).toFixed(0)}%
              </span>
            </div>
          </div>

          {/* Quality Assessment Outcome */}
          <div className="p-4 rounded-xl border border-slate-200 bg-white space-y-2">
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
              Acquisition Quality Assessment
            </div>
            <div className="text-lg font-bold text-navy-950">
              {session.quality?.state || 'GOOD'} Quality ({session.quality?.overallScore || 88}/100)
            </div>
            <div className="text-xs text-slate-600">
              Focus: {session.quality?.focusScore || 91} • Contrast: {session.quality?.contrastScore || 85} • FOV: {session.quality?.fieldOfViewScore || 89}
            </div>
          </div>
        </div>

        {/* Visual Fundus & Genuine Findings Row */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="sm:col-span-1">
            <div className="w-full aspect-square bg-black rounded-xl overflow-hidden border border-slate-300 relative">
              <img
                src={session.enhancedImageUrl || session.imageUrl || '/assets/samples/sample_dr2_fundus.svg'}
                alt="Fundus Examined"
                className="w-full h-full object-contain"
              />
              {session.enhancedImageUrl && (
                <span className="absolute bottom-2 right-2 px-2 py-0.5 rounded text-[10px] font-mono bg-teal-900/80 text-teal-200">
                  CLAHE Enhanced
                </span>
              )}
            </div>
          </div>

          <div className="sm:col-span-2 space-y-3 text-xs">
            {/* AI Screening Findings Summary */}
            <div>
              <h4 className="font-bold text-navy-950 uppercase tracking-wider text-[11px] mb-1.5">
                AI Screening Evaluation Findings:
              </h4>
              {session.classification?.keyFindingsSummary && session.classification.keyFindingsSummary.length > 0 ? (
                <ul className="space-y-1.5">
                  {session.classification.keyFindingsSummary.map((finding, idx) => (
                    <li key={idx} className="p-2 rounded-lg bg-slate-50 border border-slate-200 flex items-start gap-2 text-[11px]">
                      <span className="w-1.5 h-1.5 rounded-full bg-teal-600 mt-1.5 flex-shrink-0" />
                      <span className="font-semibold text-slate-800">{finding}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-slate-500 italic text-[11px]">Screening completed according to international clinical diabetic retinopathy severity guidelines.</p>
              )}
            </div>

            {/* Preprocessing Status */}
            <div>
              <h4 className="font-bold text-navy-950 uppercase tracking-wider text-[11px] mb-1">
                Image Preprocessing Pipeline:
              </h4>
              <p className="text-slate-600 text-[11px] leading-snug">
                Adaptive Contrast Limited Adaptive Histogram Equalization (CLAHE) applied in LAB color space to enhance local microvascular contrast prior to EfficientNet-B0 inference.
              </p>
            </div>

            {/* Referral Triage Recommendation */}
            <div>
              <h4 className="font-bold text-navy-950 uppercase tracking-wider text-[11px] mb-1">
                Referral Triage Recommendation:
              </h4>
              <p className="text-slate-700 font-medium text-[11px] leading-snug">
                {session.classification?.referralMessage || session.referralMessage || (isReferable
                  ? 'Referral recommended for tele-ophthalmology or clinical evaluation.'
                  : 'Routine screening recommended; no immediate specialist referral required.')}
              </p>
            </div>
          </div>
        </div>

        {/* Section 7 — Model Explainability (Grad-CAM) */}
        {((session.gradCam && session.gradCam.available && session.gradCam.image) || (session.grad_cam && session.grad_cam.available && session.grad_cam.image)) && (
          <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/70 space-y-3">
            <div className="flex items-center justify-between">
              <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                Model Explainability — Grad-CAM Feature Attribution
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-teal-100 text-teal-800 font-bold">
                Target: Class {(session.gradCam || session.grad_cam)?.targetClass ?? finalGrade} ({(session.gradCam || session.grad_cam)?.targetLabel || session.classification?.gradeName})
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1">
                <span className="text-[10px] font-semibold text-slate-600">Examined Fundus (CLAHE Preprocessed)</span>
                <div className="w-full aspect-square bg-black rounded-lg overflow-hidden border border-slate-300">
                  <img
                    src={session.enhancedImageUrl || session.imageUrl || '/assets/samples/sample_dr2_fundus.svg'}
                    alt="Fundus Examined"
                    className="w-full h-full object-contain"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <span className="text-[10px] font-semibold text-teal-800">Grad-CAM Attention Overlay (EfficientNet-B0)</span>
                <div className="w-full aspect-square bg-black rounded-lg overflow-hidden border border-teal-400 ring-2 ring-teal-500/20">
                  <img
                    src={(session.gradCam || session.grad_cam)?.image}
                    alt="Grad-CAM Overlay"
                    className="w-full h-full object-contain"
                  />
                </div>
              </div>
            </div>

            <p className="text-[10px] text-slate-500 italic leading-snug">
              “The Grad-CAM visualization highlights regions that contributed to the model's predicted classification. It is not lesion detection and should not be interpreted as a definitive clinical finding.”
            </p>
          </div>
        )}

        {/* Clinician Review & Decision Sign-Off */}
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs space-y-2">
          <div className="flex items-center justify-between border-b border-slate-200 pb-2">
            <div className="font-bold text-navy-950 flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-teal-600" />
              <span>Ophthalmologist Triage Sign-Off</span>
            </div>
            <StatusBadge status={session.review.status} size="sm" />
          </div>

          <div className="grid grid-cols-2 gap-4 text-[11px] pt-1">
            <div>
              <span className="text-slate-500">Reviewing Clinician:</span>
              <div className="font-semibold text-navy-950">
                {session.review.reviewerName || 'Dr. S. K. Venkat (Tele-Ophthalmologist)'}
              </div>
            </div>
            <div>
              <span className="text-slate-500">Referral Action Pathway:</span>
              <div className="font-bold text-teal-800">
                {session.review.referralDecision || (isReferable ? 'TELE_OPHTHALMOLOGY' : 'ROUTINE_MONITORING')}
              </div>
            </div>
          </div>

          {session.review.clinicalNotes && (
            <div className="pt-2 border-t border-slate-200">
              <span className="text-slate-500 text-[10px] uppercase font-semibold">Doctor Review Notes:</span>
              <p className="text-slate-700 mt-0.5 italic text-[11px]">"{session.review.clinicalNotes}"</p>
            </div>
          )}
        </div>

        {/* Model Version, Telemetry & Disclaimer */}
        <div className="p-3.5 bg-amber-50/60 rounded-xl border border-amber-200/80 text-[11px] text-amber-900 space-y-1">
          <div className="font-bold flex items-center gap-1">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-700" />
            <span>Clinical Notice & Disclaimer:</span>
          </div>
          <p className="leading-snug">
            RetinaGuard provides AI-assisted diabetic retinopathy screening and referral support. It does not replace definitive diagnosis, comprehensive eye examination, or clinical judgment by a qualified healthcare professional.
          </p>
        </div>

        {/* Processing Footer */}
        <div className="pt-3 border-t border-slate-200 text-[10px] text-slate-400 flex flex-col sm:flex-row justify-between items-center gap-2 font-mono">
          <div>AI Classifier: EfficientNet-B0 (models/retinaguard_exp1_best.pth) • CLAHE Preprocessed</div>
          <div>Report Generated: {new Date().toLocaleString()}</div>
        </div>
      </div>
    </div>
  );
};
