import React from 'react';
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  ArrowRight,
  Sparkles,
  RefreshCw,
  Upload,
  Focus,
  Sun,
  Sliders,
  Maximize2,
  Lock,
  Camera
} from 'lucide-react';
import { Button } from '../common/Button';
import { Card } from '../common/Card';
import { StatusBadge } from '../common/StatusBadge';
import { QualityMetrics, QualityState } from '../../types';

interface QualityAssessmentProps {
  imageUrl: string;
  quality: QualityMetrics;
  onSetQuality: (quality: QualityMetrics) => void;
  onNext: () => void;
  onBack: () => void;
  onRecapture: () => void;
}

export const QualityAssessment: React.FC<QualityAssessmentProps> = ({
  imageUrl,
  quality,
  onSetQuality,
  onNext,
  onBack,
  onRecapture,
}) => {
  const isUngradable = quality.state === 'UNGRADABLE';
  const isBorderline = quality.state === 'BORDERLINE';
  const isGood = quality.state === 'GOOD';

  const dimensions = [
    { label: 'Sharpness & Blur', score: quality.focusScore, threshold: 75, icon: Focus },
    { label: 'Illumination Level', score: quality.illuminationScore, threshold: 70, icon: Sun },
    { label: 'Vessel Contrast', score: quality.contrastScore, threshold: 75, icon: Sliders },
    { label: 'Field of View / Framing', score: quality.fieldOfViewScore, threshold: 80, icon: Maximize2 },
  ];

  return (
    <div className="space-y-6">
      {/* Step Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-navy-950">Step 3 — Image Quality Check</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Automated image validation ensuring the photograph is clear and usable before running AI analysis.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={onBack}>
            Back to Upload
          </Button>

          {isUngradable ? (
            <Button
              variant="danger"
              size="sm"
              onClick={onRecapture}
              leftIcon={<RefreshCw className="w-4 h-4" />}
            >
              Upload Another Image
            </Button>
          ) : (
            <Button
              variant="teal"
              size="sm"
              onClick={onNext}
              rightIcon={<ArrowRight className="w-4 h-4" />}
            >
              Proceed to CLAHE Enhancement →
            </Button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Image Preview & Primary Simple Result (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <Card title="Retinal Image Quality Result">
            <div className="space-y-4">
              <div className="w-60 h-60 mx-auto rounded-2xl overflow-hidden border border-slate-800/90 shadow-sm bg-black relative flex items-center justify-center">
                <img src={imageUrl} alt="Fundus Image" className="w-full h-full object-contain" />
              </div>

              {/* Prominent Simple Result Badge */}
              <div
                className={`p-4 rounded-xl border text-center space-y-1.5 ${
                  isGood
                    ? 'bg-emerald-50 border-emerald-200 text-emerald-950'
                    : isBorderline
                    ? 'bg-amber-50 border-amber-200 text-amber-950'
                    : 'bg-rose-50 border-rose-200 text-rose-950'
                }`}
              >
                <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
                  Validation Outcome
                </div>
                <div className="text-lg font-bold flex items-center justify-center gap-2">
                  {isGood ? (
                    <>
                      <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                      <span>Image Quality: Gradable (Good)</span>
                    </>
                  ) : isBorderline ? (
                    <>
                      <AlertTriangle className="w-5 h-5 text-amber-600" />
                      <span>Image Quality: Borderline</span>
                    </>
                  ) : (
                    <>
                      <XCircle className="w-5 h-5 text-rose-600" />
                      <span>Image Quality: Ungradable (Recapture)</span>
                    </>
                  )}
                </div>
                <div className="text-xs font-medium text-slate-600">
                  Overall Quality Score: <span className="font-bold text-navy-950">{quality.overallScore}</span> / 100
                </div>
              </div>
            </div>
          </Card>
        </div>

        {/* Right Column: Detailed Criteria & Warning/Instructions (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          {/* If Quality is Poor: Clear Warning & Recapture Actions */}
          {isUngradable ? (
            <div className="p-5 rounded-2xl border-2 border-rose-300 bg-rose-50/90 text-rose-950 space-y-4 shadow-sm">
              <div className="flex items-start gap-3">
                <Lock className="w-6 h-6 text-rose-600 flex-shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <h3 className="font-bold text-base text-rose-900">
                    Image quality is insufficient for reliable screening.
                  </h3>
                  <p className="text-xs text-rose-800 leading-relaxed">
                    The retinal photograph is too blurry, dark, or occluded for the AI model to safely evaluate. Downstream analysis is blocked to prevent missing real lesions.
                  </p>
                </div>
              </div>

              {quality.recaptureGuidance && quality.recaptureGuidance.length > 0 && (
                <div className="p-3.5 bg-white/80 rounded-xl border border-rose-200 space-y-1.5 text-xs text-rose-900">
                  <div className="font-bold flex items-center gap-1.5">
                    <Camera className="w-4 h-4 text-rose-600" />
                    <span>How to fix for recapture:</span>
                  </div>
                  <ul className="list-disc list-inside space-y-1 pl-1 text-[11px] text-rose-800">
                    {quality.recaptureGuidance.map((g, i) => (
                      <li key={i}>{g}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Requirement 6: Two clear action buttons */}
              <div className="pt-2 flex flex-col sm:flex-row gap-2.5">
                <Button
                  variant="danger"
                  size="md"
                  onClick={onRecapture}
                  leftIcon={<Upload className="w-4 h-4" />}
                  className="w-full sm:w-auto"
                >
                  Upload Another Image
                </Button>
                <Button
                  variant="outline"
                  size="md"
                  onClick={onRecapture}
                  leftIcon={<RefreshCw className="w-4 h-4" />}
                  className="w-full sm:w-auto bg-white hover:bg-slate-50"
                >
                  Recapture Image
                </Button>
              </div>
            </div>
          ) : isBorderline ? (
            <div className="p-4 rounded-xl border border-amber-200 bg-amber-50 text-amber-950 space-y-2">
              <div className="flex items-center gap-2 font-bold text-sm text-amber-900">
                <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0" />
                <span>Image quality is acceptable but enhancement is recommended.</span>
              </div>
              <p className="text-xs text-amber-800 leading-relaxed">
                The image has slight uneven lighting or low contrast. The next preprocessing step will enhance illumination and vessels using CLAHE filtering.
              </p>
            </div>
          ) : (
            <div className="p-4 rounded-xl border border-emerald-200 bg-emerald-50 text-emerald-950 space-y-2">
              <div className="flex items-center gap-2 font-bold text-sm text-emerald-900">
                <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
                <span>Image quality is sufficient for automated screening.</span>
              </div>
              <p className="text-xs text-emerald-800 leading-relaxed">
                Focus, illumination, and retinal framing meet clinical screening standards. You may proceed to preprocessing and AI analysis.
              </p>
            </div>
          )}

          {/* Simple Quality Indicators */}
          <Card title="Quality Indicators Checked" subtitle="Basic checks performed on the fundus photograph">
            <div className="space-y-3">
              {dimensions.map((d, i) => {
                const Icon = d.icon;
                const isPassing = d.score >= d.threshold;
                return (
                  <div key={i} className="p-3 rounded-lg border border-slate-100 bg-white flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2.5 font-semibold text-slate-700">
                      <Icon className="w-4 h-4 text-slate-500" />
                      <span>{d.label}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`font-mono font-bold ${isPassing ? 'text-emerald-700' : 'text-rose-600'}`}>
                        {d.score} / 100
                      </span>
                      {isPassing ? (
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
                          Pass
                        </span>
                      ) : (
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-rose-100 text-rose-800">
                          Low
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};
