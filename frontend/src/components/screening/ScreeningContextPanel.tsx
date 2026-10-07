import React, { useState } from 'react';
import {
  ShieldAlert,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  Save,
  Eye,
  User,
  Activity,
  Layers,
  Sparkles,
  ChevronRight,
  ChevronDown
} from 'lucide-react';
import { Button } from '../common/Button';
import { StatusBadge } from '../common/StatusBadge';
import { Modal } from '../common/Modal';
import {
  DRPrediction,
  QualityMetrics,
  LesionFinding,
  ClinicalReview
} from '../../types';
import { PatientFormData } from './PatientStep';

interface ScreeningContextPanelProps {
  screeningId: string;
  patientData: PatientFormData;
  quality: QualityMetrics;
  classification: DRPrediction;
  lesions: LesionFinding[];
  review: ClinicalReview;
  currentStep: number;
  onReset: () => void;
}

export const ScreeningContextPanel: React.FC<ScreeningContextPanelProps> = ({
  screeningId,
  patientData,
  quality,
  classification,
  lesions,
  review,
  currentStep,
  onReset,
}) => {
  const [showResetConfirm, setShowResetConfirm] = useState(false);
  const [isSavedDraft, setIsSavedDraft] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);

  const isReferable = classification.grade >= 2;

  const handleSaveDraft = () => {
    setIsSavedDraft(true);
    setTimeout(() => setIsSavedDraft(false), 3000);
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200/90 shadow-card-subtle overflow-hidden text-xs">
      {/* Panel Header */}
      <div
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="p-4 bg-navy-950 text-white flex items-center justify-between cursor-pointer select-none"
      >
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-teal-400" />
          <span className="font-bold text-sm tracking-tight">Active Screening Session</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-navy-850 text-slate-300">
            {screeningId}
          </span>
          <button className="text-slate-400 hover:text-white">
            {isCollapsed ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4 rotate-90" />}
          </button>
        </div>
      </div>

      {!isCollapsed && (
        <div className="p-4 space-y-4">
          {/* Patient Quick Strip */}
          <div className="p-3 rounded-lg bg-slate-50 border border-slate-200/80 space-y-1">
            <div className="flex items-center justify-between text-slate-500 text-[10px] uppercase font-bold">
              <span>Candidate</span>
              <span className="text-teal-700 font-bold font-mono">
                {patientData.eye === 'OD' ? 'Right Eye (OD)' : patientData.eye === 'OS' ? 'Left Eye (OS)' : 'Not Specified'}
              </span>
            </div>
            <div className="font-bold text-navy-950 text-sm truncate">
              {patientData.name || 'Candidate Not Selected'}
            </div>
            <div className="text-[11px] text-slate-500 truncate">
              {patientData.patientId} • {patientData.age ? `${patientData.age} yrs` : '—'} • {patientData.sex}
            </div>
          </div>

          {/* Quality Indicator */}
          <div className="flex items-center justify-between p-2.5 rounded-lg border border-slate-100 bg-white">
            <span className="text-slate-500 text-[11px] font-medium">Quality Check:</span>
            <StatusBadge status={quality.state} size="sm" />
          </div>

          {/* Diagnostic Triage Status */}
          <div className="p-3 rounded-lg bg-slate-50 border border-slate-200/80 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-slate-500 text-[10px] uppercase font-bold">Live AI Staging</span>
              <StatusBadge status={isReferable ? 'REFERABLE' : 'NON-REFERABLE'} size="sm" />
            </div>

            <div className="text-navy-950 font-black text-sm">
              Level {classification.grade} — {classification.gradeName}
            </div>

            <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1 border-t border-slate-200 font-mono">
              <span>Confidence:</span>
              <span className="font-bold text-teal-700">{(classification.confidence * 100).toFixed(0)}%</span>
            </div>
          </div>

          {/* Screening Review Status */}
          <div className="space-y-1.5 pt-1">
            <div className="text-slate-500 text-[10px] uppercase font-bold">Clinical Status:</div>
            <div className="grid grid-cols-2 gap-1.5 text-[11px]">
              <div className="p-2 bg-slate-50 rounded border border-slate-200 text-slate-700">
                Triage: <span className="font-bold text-navy-950">{isReferable ? 'Refer' : 'Routine'}</span>
              </div>
              <div className="p-2 bg-slate-50 rounded border border-slate-200 text-slate-700">
                Review: <span className="font-bold text-navy-950">{review.status}</span>
              </div>
            </div>
          </div>

          {/* Quick Action Buttons */}
          <div className="pt-2 border-t border-slate-100 space-y-2">
            <Button
              variant="outline"
              size="sm"
              className="w-full text-xs"
              onClick={handleSaveDraft}
              leftIcon={<Save className="w-3.5 h-3.5" />}
            >
              {isSavedDraft ? 'Session Draft Saved' : 'Save Session Draft'}
            </Button>

            <Button
              variant="ghost"
              size="sm"
              className="w-full text-xs text-rose-600 hover:text-rose-700 hover:bg-rose-50"
              onClick={() => setShowResetConfirm(true)}
              leftIcon={<RotateCcw className="w-3.5 h-3.5" />}
            >
              Reset / Start Over
            </Button>
          </div>
        </div>
      )}

      {/* Reset Confirmation Modal */}
      {showResetConfirm && (
        <Modal
          isOpen={true}
          onClose={() => setShowResetConfirm(false)}
          title="Reset Active Screening Session?"
          subtitle="All unsaved screening progress for this session will be cleared."
          maxWidth="sm"
        >
          <div className="space-y-4 text-xs">
            <p className="text-slate-600">
              Are you sure you want to reset the current screening case? This will return you to Step 1.
            </p>
            <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
              <Button variant="ghost" size="sm" onClick={() => setShowResetConfirm(false)}>
                Cancel
              </Button>
              <Button
                variant="danger"
                size="sm"
                onClick={() => {
                  setShowResetConfirm(false);
                  onReset();
                }}
              >
                Confirm Reset
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
