import React from 'react';
import { ArrowRight, Award, AlertCircle, CheckCircle2, ShieldAlert, Info, HelpCircle } from 'lucide-react';
import { Button } from '../common/Button';
import { Card } from '../common/Card';
import { StatusBadge } from '../common/StatusBadge';
import { DRPrediction, DRGrade, GradCamResult } from '../../types';

interface DRClassificationProps {
  classification: DRPrediction;
  gradCam?: GradCamResult;
  fundusImageUrl?: string;
  onNext: () => void;
  onBack: () => void;
  onOverrideGrade?: (grade: DRGrade) => void;
}

const DR_LEVELS = [
  { grade: 0, label: 'Level 0 — No Diabetic Retinopathy', desc: 'No microaneurysms, hemorrhages, or lipid exudates detected.', referable: false },
  { grade: 1, label: 'Level 1 — Mild NPDR', desc: 'Microaneurysms only. Non-referable baseline stage.', referable: false },
  { grade: 2, label: 'Level 2 — Moderate NPDR', desc: 'More than microaneurysms; lipid exudates or minor hemorrhages present.', referable: true },
  { grade: 3, label: 'Level 3 — Severe NPDR', desc: '4-2-1 rule: Extensive intraretinal hemorrhages or venous beading.', referable: true },
  { grade: 4, label: 'Level 4 — Proliferative DR', desc: 'Neovascularization fronds or preretinal/vitreous hemorrhage.', referable: true },
];

export const DRClassification: React.FC<DRClassificationProps> = ({
  classification,
  gradCam,
  fundusImageUrl,
  onNext,
  onBack,
}) => {
  const isReferable = classification.grade >= 2;

  const levelStyles: Record<number, { border: string; bg: string; text: string }> = {
    0: { border: 'border-emerald-200', bg: 'bg-emerald-50/40', text: 'text-emerald-900' },
    1: { border: 'border-amber-200', bg: 'bg-amber-50/40', text: 'text-amber-900' },
    2: { border: 'border-orange-200', bg: 'bg-orange-50/40', text: 'text-orange-900' },
    3: { border: 'border-rose-200', bg: 'bg-rose-50/40', text: 'text-rose-900' },
    4: { border: 'border-purple-200', bg: 'bg-purple-50/40', text: 'text-purple-950' },
  };

  const currentStyle = levelStyles[classification.grade] || levelStyles[0];

  return (
    <div className="space-y-6">
      {/* Step Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-navy-950">Step 5 — AI Diabetic Retinopathy Assessment</h2>
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-teal-50 text-teal-800 border border-teal-200">
              EfficientNet-B0 • Decision Support
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Automated screening prediction staged according to international clinical diabetic retinopathy severity guidelines.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={onBack}>
            Back
          </Button>
          <Button variant="teal" size="sm" onClick={onNext} rightIcon={<ArrowRight className="w-4 h-4" />}>
            Proceed to Clinical Review →
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Primary AI Screening Result (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          <Card className={`border ${currentStyle.border} ${currentStyle.bg}`}>
            <div className="space-y-5">
              {/* Top Row: AI Screening Result */}
              <div className="flex items-start justify-between">
                <div>
                  <span className="text-[11px] font-bold tracking-wider text-slate-500 uppercase">
                    AI Screening Result
                  </span>
                  <h3 className="text-2xl font-black text-navy-950 mt-1">
                    {classification.gradeName}
                  </h3>
                  <div className="text-sm font-bold text-teal-800 mt-0.5">
                    DR Level {classification.grade}
                  </div>
                </div>

                <div className="flex flex-col items-end gap-1">
                  <span className="text-[10px] text-slate-500 uppercase font-semibold">AI Confidence</span>
                  <div className="text-lg font-mono font-black text-navy-950 bg-white/80 px-3 py-1 rounded-lg border border-slate-200 shadow-sm">
                    {(classification.confidence * 100).toFixed(0)}%
                  </div>
                </div>
              </div>

              {/* Requirement 9: Referral Status Card */}
              <div
                className={`p-4 rounded-xl border flex items-center justify-between ${
                  isReferable
                    ? 'bg-orange-50 border-orange-200 text-orange-950'
                    : 'bg-emerald-50 border-emerald-200 text-emerald-950'
                }`}
              >
                <div className="flex items-center gap-3">
                  {isReferable ? (
                    <ShieldAlert className="w-6 h-6 text-orange-600 flex-shrink-0" />
                  ) : (
                    <CheckCircle2 className="w-6 h-6 text-emerald-600 flex-shrink-0" />
                  )}
                  <div>
                    <div className="text-xs font-bold uppercase tracking-wide text-slate-600">
                      Referral Status
                    </div>
                    <div className="font-extrabold text-base">
                      {isReferable ? 'Referable DR' : 'No Referable DR Detected'}
                    </div>
                    <p className="text-xs opacity-90 mt-0.5">
                      {classification.referralMessage || (isReferable
                        ? 'Referral to ophthalmologist or tertiary center recommended for clinical examination.'
                        : 'No signs of referable diabetic retinopathy detected at this screening. Continue routine community follow-up.')}
                    </p>
                  </div>
                </div>

                <StatusBadge status={isReferable ? 'REFERABLE' : 'NON-REFERABLE'} size="md" />
              </div>

              {/* Mandatory Clinical Disclaimer (Requirement 9) */}
              <div className="p-3 bg-white/70 rounded-xl border border-slate-200 text-xs text-slate-600 leading-relaxed flex items-start gap-2">
                <Info className="w-4 h-4 text-slate-400 flex-shrink-0 mt-0.5" />
                <span>
                  <strong>Clinical Notice: </strong> AI-assisted screening result. "No Referable DR Detected" does not replace a comprehensive eye examination. Final clinical assessment should be performed by a qualified healthcare professional.
                </span>
              </div>

              {/* Findings Summary */}
              <div className="space-y-2 pt-2 border-t border-slate-200/70">
                <span className="text-xs font-bold text-navy-950 uppercase tracking-wider">
                  Summary Findings:
                </span>
                <ul className="space-y-1.5 text-xs text-slate-700">
                  {classification.keyFindingsSummary.map((finding, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-teal-600 mt-1.5 flex-shrink-0" />
                      <span>{finding}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </Card>

          {/* Model Class Probabilities */}
          <Card title="Classification Distribution" subtitle="Confidence distribution across the 5 clinical stages">
            <div className="space-y-3">
              {Object.entries(classification.classProbabilities).map(([label, prob], idx) => {
                const isSelected = idx === classification.grade;
                return (
                  <div key={label} className="space-y-1 text-xs">
                    <div className="flex justify-between font-medium">
                      <span className={isSelected ? 'text-navy-950 font-bold' : 'text-slate-600'}>
                        {label}
                      </span>
                      <span className="font-mono font-bold text-slate-800">
                        {(prob * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                      <div
                        style={{ width: `${prob * 100}%` }}
                        className={`h-full transition-all ${
                          isSelected ? 'bg-teal-600' : 'bg-slate-300'
                        }`}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>
        </div>

        {/* Right Column: ICDR 5-Level Reference Guide (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <Card title="Standard 5-Level DR Scale" subtitle="International clinical diabetic retinopathy scale">
            <div className="space-y-2.5">
              {DR_LEVELS.map((lvl) => {
                const isCurrent = lvl.grade === classification.grade;
                return (
                  <div
                    key={lvl.grade}
                    className={`p-3 rounded-xl border text-xs transition-all ${
                      isCurrent
                        ? 'bg-teal-50 border-teal-500 ring-2 ring-teal-400/20'
                        : 'bg-white border-slate-200'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="font-bold text-navy-950 flex items-center gap-2">
                        <span>{lvl.label}</span>
                        {isCurrent && (
                          <span className="text-[10px] font-bold px-1.5 py-0.2 rounded bg-teal-600 text-white">
                            Predicted
                          </span>
                        )}
                      </div>
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                          lvl.referable
                            ? 'bg-orange-100 text-orange-800'
                            : 'bg-emerald-100 text-emerald-800'
                        }`}
                      >
                        {lvl.referable ? 'Referable' : 'Non-Referable'}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-500 mt-1 leading-normal">{lvl.desc}</p>
                  </div>
                );
              })}
            </div>
          </Card>
        </div>
      </div>

      {/* Genuine Model Explainability (Grad-CAM) */}
      {gradCam && gradCam.available && gradCam.image && (
        <Card
          title="Model Explainability — Grad-CAM"
          subtitle="Visual feature attribution from trained EfficientNet-B0 for the predicted classification"
        >
          <div className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-navy-950 uppercase tracking-wide">
                    Examined Fundus (CLAHE Preprocessed)
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-100 text-slate-700">
                    Input Image
                  </span>
                </div>
                <div className="aspect-square w-full max-w-md mx-auto bg-black rounded-xl overflow-hidden border border-slate-200 shadow-inner flex items-center justify-center">
                  <img
                    src={fundusImageUrl || '/assets/samples/sample_dr2_fundus.svg'}
                    alt="Examined Fundus"
                    className="w-full h-full object-contain"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-teal-800 uppercase tracking-wide">
                    Grad-CAM Attention Overlay
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-teal-100 text-teal-800 font-mono">
                    Target: Class {gradCam.targetClass ?? classification.grade} ({gradCam.targetLabel || classification.gradeName})
                  </span>
                </div>
                <div className="aspect-square w-full max-w-md mx-auto bg-black rounded-xl overflow-hidden border border-teal-300 ring-2 ring-teal-500/20 shadow-inner flex items-center justify-center">
                  <img
                    src={gradCam.image}
                    alt="Grad-CAM Overlay"
                    className="w-full h-full object-contain"
                  />
                </div>
              </div>
            </div>

            <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-600 leading-relaxed flex items-start gap-2.5">
              <Info className="w-4 h-4 text-teal-600 flex-shrink-0 mt-0.5" />
              <span>
                <strong>Explainability Notice: </strong>
                Grad-CAM highlights image regions that contributed to the model's predicted classification. It is an explainability visualization and does not constitute lesion detection or a medical diagnosis.
              </span>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};
