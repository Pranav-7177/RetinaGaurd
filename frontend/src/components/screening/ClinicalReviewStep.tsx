import React, { useState } from 'react';
import {
  ArrowRight,
  UserCheck,
  CheckCircle2,
  Edit3,
  RefreshCw,
  FileText,
  AlertCircle,
  Send,
  ShieldCheck,
  Layers,
  Sparkles,
  Info
} from 'lucide-react';
import { Button } from '../common/Button';
import { Card } from '../common/Card';
import { StatusBadge } from '../common/StatusBadge';
import {
  DRPrediction,
  ClinicalReview,
  DRGrade,
  ReferralDecision,
  QualityMetrics,
  LesionFinding,
  ExplainabilityResult,
  GradCamResult
} from '../../types';

interface ClinicalReviewStepProps {
  classification: DRPrediction;
  quality?: QualityMetrics;
  lesions: LesionFinding[];
  explainability?: ExplainabilityResult;
  gradCam?: GradCamResult;
  fundusImageUrl?: string;
  review: ClinicalReview;
  onSubmitReview: (review: ClinicalReview) => void;
  onNext: () => void;
  onBack: () => void;
}

export const ClinicalReviewStep: React.FC<ClinicalReviewStepProps> = ({
  classification,
  quality,
  lesions,
  explainability,
  gradCam,
  fundusImageUrl,
  review,
  onSubmitReview,
  onNext,
  onBack,
}) => {
  const [selectedGrade, setSelectedGrade] = useState<DRGrade>(
    review.assignedGrade !== undefined ? review.assignedGrade : classification.grade
  );
  const [referralDecision, setReferralDecision] = useState<ReferralDecision>(
    review.referralDecision || (classification.grade >= 2 ? 'TELE_OPHTHALMOLOGY' : 'ROUTINE_MONITORING')
  );
  const [notes, setNotes] = useState(
    review.clinicalNotes || (classification.grade >= 2
      ? 'Confirmed moderate NPDR with macular exudates. Recommend optical coherence tomography (OCT) and district clinic follow-up.'
      : 'Clear background fundus confirmed. Routine community screening in 12 months.')
  );
  const [reviewerName, setReviewerName] = useState(
    review.reviewerName || 'Dr. S. K. Venkat (Tele-Ophthalmologist)'
  );
  const [actionType, setActionType] = useState<'CONFIRM' | 'MODIFY' | 'REACQUIRE'>('CONFIRM');

  const isAgreed = selectedGrade === classification.grade && actionType === 'CONFIRM';

  const handleConfirm = () => {
    onSubmitReview({
      status: 'CONFIRMED',
      reviewerName,
      reviewedAt: new Date().toLocaleString(),
      assignedGrade: classification.grade,
      referralDecision: classification.grade >= 2 ? 'TELE_OPHTHALMOLOGY' : 'ROUTINE_MONITORING',
      clinicalNotes: notes,
      agreementStatus: 'AGREED',
    });
    onNext();
  };

  const handleModify = () => {
    onSubmitReview({
      status: 'MODIFIED',
      reviewerName,
      reviewedAt: new Date().toLocaleString(),
      assignedGrade: selectedGrade,
      referralDecision,
      clinicalNotes: notes,
      agreementStatus: 'MODIFIED',
    });
    onNext();
  };

  const handleReacquire = () => {
    onSubmitReview({
      status: 'REACQUISITION_REQUESTED',
      reviewerName,
      reviewedAt: new Date().toLocaleString(),
      assignedGrade: selectedGrade,
      referralDecision: 'ROUTINE_MONITORING',
      clinicalNotes: notes,
      reacquisitionReason: 'Image clarity sub-optimal for conclusive clinical adjudication.',
      agreementStatus: 'REACQUISITION_REQUESTED',
    });
    onNext();
  };

  return (
    <div className="space-y-6">
      {/* Step Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-navy-950">Step 6 — Human-in-the-Loop Clinical Review</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Ophthalmologist review of AI model staging, model confidence, and referral triage decision.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={onBack}>
            Back
          </Button>
          <Button variant="teal" size="sm" onClick={onNext} rightIcon={<ArrowRight className="w-4 h-4" />}>
            Generate Final Screening Report
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Reviewer Action Form (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          <Card title="Clinician Adjudication Workspace">
            <div className="space-y-5 text-xs">
              {/* Action Selection Tabs */}
              <div>
                <label className="block font-bold text-slate-700 mb-2">Reviewer Decision Action:</label>
                <div className="grid grid-cols-3 gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      setActionType('CONFIRM');
                      setSelectedGrade(classification.grade);
                    }}
                    className={`py-2.5 px-3 rounded-xl border font-semibold flex items-center justify-center gap-2 transition-all ${
                      actionType === 'CONFIRM'
                        ? 'bg-emerald-600 text-white border-emerald-600 shadow-sm'
                        : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
                    }`}
                  >
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Confirm AI Grade</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setActionType('MODIFY')}
                    className={`py-2.5 px-3 rounded-xl border font-semibold flex items-center justify-center gap-2 transition-all ${
                      actionType === 'MODIFY'
                        ? 'bg-indigo-600 text-white border-indigo-600 shadow-sm'
                        : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
                    }`}
                  >
                    <Edit3 className="w-4 h-4" />
                    <span>Modify DR Grade</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setActionType('REACQUIRE')}
                    className={`py-2.5 px-3 rounded-xl border font-semibold flex items-center justify-center gap-2 transition-all ${
                      actionType === 'REACQUIRE'
                        ? 'bg-rose-600 text-white border-rose-600 shadow-sm'
                        : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
                    }`}
                  >
                    <RefreshCw className="w-4 h-4" />
                    <span>Request Recapture</span>
                  </button>
                </div>
              </div>

              {/* Reviewer Details Row */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Reviewing Clinician Name</label>
                  <input
                    type="text"
                    value={reviewerName}
                    onChange={(e) => setReviewerName(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20 text-xs"
                  />
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Referral Action Pathway</label>
                  <select
                    value={referralDecision}
                    onChange={(e) => setReferralDecision(e.target.value as any)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20 text-xs text-slate-800"
                  >
                    <option value="ROUTINE_MONITORING">Routine Annual Monitoring (Level 0–1)</option>
                    <option value="TELE_OPHTHALMOLOGY">Tele-Ophthalmology Consultation (Level 2)</option>
                    <option value="URGENT_TERTIARY">Urgent Tertiary Eye Hospital Referral (Level 3–4)</option>
                    <option value="NO_REFERRAL">No Referral Required</option>
                  </select>
                </div>
              </div>

              {/* DR Grade Selector when Modifying */}
              {actionType === 'MODIFY' && (
                <div className="p-3.5 bg-indigo-50 rounded-xl border border-indigo-200 space-y-2">
                  <label className="block font-bold text-indigo-950">
                    Select Adjusted Clinical Grade (Overriding AI Level {classification.grade}):
                  </label>
                  <div className="grid grid-cols-5 gap-1.5">
                    {[0, 1, 2, 3, 4].map((g) => (
                      <button
                        key={g}
                        type="button"
                        onClick={() => setSelectedGrade(g as DRGrade)}
                        className={`py-2 text-center rounded-lg border text-xs font-bold transition-all ${
                          selectedGrade === g
                            ? 'bg-indigo-600 text-white border-indigo-700 shadow-sm'
                            : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-100'
                        }`}
                      >
                        Level {g}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Doctor Review Notes */}
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Clinical Review Notes & Impressions</label>
                <textarea
                  rows={3}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Enter clinical impression, treatment instructions, or reacquisition rationale..."
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20 text-xs"
                />
              </div>

              {/* Concordance Tracking Status */}
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between text-xs">
                <div>
                  <span className="text-slate-500 text-[10px] uppercase font-semibold">AI vs Doctor Concordance:</span>
                  <div className="font-bold text-navy-950">
                    {actionType === 'CONFIRM' ? 'Agreement (Concordant)' : actionType === 'MODIFY' ? `Disagreement (AI: Lvl ${classification.grade} → Doc: Lvl ${selectedGrade})` : 'Reacquisition Requested'}
                  </div>
                </div>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                  actionType === 'CONFIRM' ? 'bg-emerald-100 text-emerald-800' : 'bg-indigo-100 text-indigo-800'
                }`}>
                  {actionType === 'CONFIRM' ? 'AGREED' : 'OVERRIDDEN'}
                </span>
              </div>

              {/* Submit Buttons */}
              <div className="pt-2 flex justify-end gap-2">
                {actionType === 'CONFIRM' && (
                  <Button variant="teal" onClick={handleConfirm} leftIcon={<Send className="w-4 h-4" />}>
                    Confirm & Save AI Staging
                  </Button>
                )}
                {actionType === 'MODIFY' && (
                  <Button variant="primary" onClick={handleModify} leftIcon={<Edit3 className="w-4 h-4" />}>
                    Save Modified Grade (Level {selectedGrade})
                  </Button>
                )}
                {actionType === 'REACQUIRE' && (
                  <Button variant="danger" onClick={handleReacquire} leftIcon={<RefreshCw className="w-4 h-4" />}>
                    Submit Recapture Request
                  </Button>
                )}
              </div>
            </div>
          </Card>
        </div>

        {/* Right Column: AI Evidence Summary to Review (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <Card title="AI Screening Summary to Validate">
            <div className="space-y-3.5 text-xs">
              {/* Staging */}
              <div className="flex items-center justify-between p-3 bg-slate-50 rounded-xl border border-slate-200">
                <div>
                  <span className="text-slate-400 text-[10px] uppercase font-semibold">AI Prediction</span>
                  <div className="font-bold text-navy-950 text-sm">
                    Level {classification.grade} — {classification.gradeName}
                  </div>
                </div>
                <StatusBadge status={classification.grade >= 2 ? 'REFERABLE' : 'NON-REFERABLE'} size="sm" />
              </div>

              {/* Confidence & Image Quality */}
              <div className="grid grid-cols-2 gap-2">
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                  <span className="text-slate-400 text-[10px] uppercase font-semibold">Confidence</span>
                  <div className="font-mono font-bold text-teal-700 text-sm mt-0.5">
                    {(classification.confidence * 100).toFixed(1)}%
                  </div>
                </div>

                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                  <span className="text-slate-400 text-[10px] uppercase font-semibold">Image Quality</span>
                  <div className="font-bold text-emerald-700 text-sm mt-0.5">
                    {quality?.state || 'GOOD'} ({quality?.overallScore || 88}/100)
                  </div>
                </div>
              </div>

              {/* Summary Key Findings */}
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-1.5">
                <div className="font-bold text-navy-950">Model Staging Summary:</div>
                <ul className="list-disc list-inside space-y-1 text-[11px] text-slate-700">
                  {classification.keyFindingsSummary.map((finding, idx) => (
                    <li key={idx}>{finding}</li>
                  ))}
                </ul>
              </div>

              {/* Referral Guidance */}
              {classification.referralMessage && (
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-1">
                  <div className="font-bold text-navy-950">Referral Guidance:</div>
                  <p className="text-[11px] text-slate-600">
                    {classification.referralMessage}
                  </p>
                </div>
              )}
            </div>
          </Card>

          {/* Grad-CAM Model Attention Card */}
          {gradCam && gradCam.available && gradCam.image && (
            <Card
              title="Grad-CAM Attention Map"
              subtitle={`Target Class ${gradCam.targetClass ?? classification.grade} (${gradCam.targetLabel || classification.gradeName})`}
            >
              <div className="space-y-2.5">
                <div className="w-full aspect-square bg-black rounded-xl overflow-hidden border border-teal-300 ring-2 ring-teal-500/20 flex items-center justify-center">
                  <img
                    src={gradCam.image}
                    alt="Grad-CAM Overlay"
                    className="w-full h-full object-contain"
                  />
                </div>
                <p className="text-[10px] text-slate-500 italic leading-snug">
                  Grad-CAM visualizes model attention for the predicted class. It is an explainability tool, not lesion detection.
                </p>
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};
