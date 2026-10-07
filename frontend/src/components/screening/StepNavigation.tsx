import React from 'react';
import {
  User,
  Upload,
  CheckCircle2,
  Sparkles,
  Award,
  UserCheck,
  FileText,
  Check,
  Lock,
  Ban
} from 'lucide-react';
import { StepState } from '../../types';

export interface StepItemConfig {
  step: number;
  label: string;
  shortLabel: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
}

export const SCREENING_STEPS_CONFIG: StepItemConfig[] = [
  { step: 1, label: 'Patient', shortLabel: 'Patient', icon: User, description: 'Demographics' },
  { step: 2, label: 'Image', shortLabel: 'Image', icon: Upload, description: 'Fundus Capture' },
  { step: 3, label: 'Quality', shortLabel: 'Quality', icon: CheckCircle2, description: 'Quality Gate' },
  { step: 4, label: 'Enhancement', shortLabel: 'CLAHE', icon: Sparkles, description: 'Adaptive CLAHE' },
  { step: 5, label: 'Classification', shortLabel: 'DR Grade', icon: Award, description: 'EfficientNet-B0' },
  { step: 6, label: 'Clinical Review', shortLabel: 'Review', icon: UserCheck, description: 'Doctor Validation' },
  { step: 7, label: 'Report', shortLabel: 'Report', icon: FileText, description: 'Screening Result' },
];

interface StepNavigationProps {
  currentStep: number;
  onSelectStep: (step: number) => void;
  getStepStatus: (step: number) => StepState;
}

export const StepNavigation: React.FC<StepNavigationProps> = ({
  currentStep,
  onSelectStep,
  getStepStatus,
}) => {
  return (
    <div className="bg-white rounded-xl border border-slate-200/90 p-4 shadow-card-subtle mb-5 overflow-x-auto">
      <div className="flex items-center justify-between min-w-[820px] gap-2">
        {SCREENING_STEPS_CONFIG.map((s, index) => {
          const Icon = s.icon;
          const status = getStepStatus(s.step);
          const isCurrent = status === 'current';
          const isCompleted = status === 'completed';
          const isBlocked = status === 'blocked';
          const isUpcoming = status === 'upcoming';

          return (
            <React.Fragment key={s.step}>
              <button
                type="button"
                onClick={() => !isBlocked && onSelectStep(s.step)}
                disabled={isBlocked || isUpcoming}
                title={
                  isBlocked
                    ? `Step ${s.step}: Blocked (Resolve prior step or ungradable image)`
                    : isCompleted
                    ? `Step ${s.step}: Completed - Click to revisit`
                    : isCurrent
                    ? `Step ${s.step}: Current Active Step`
                    : `Step ${s.step}: Complete previous steps to unlock`
                }
                className={`flex flex-col items-center group relative focus:outline-none transition-all ${
                  isBlocked
                    ? 'opacity-45 cursor-not-allowed'
                    : isUpcoming
                    ? 'opacity-60 cursor-not-allowed'
                    : 'cursor-pointer'
                }`}
              >
                {/* Step Circle */}
                <div
                  className={`w-9 h-9 rounded-xl flex items-center justify-center text-xs font-bold transition-all relative ${
                    isCurrent
                      ? 'bg-teal-600 text-white ring-4 ring-teal-500/20 shadow-sm'
                      : isCompleted
                      ? 'bg-teal-50 text-teal-800 border border-teal-200/80'
                      : isBlocked
                      ? 'bg-rose-50 text-rose-600 border border-rose-200'
                      : 'bg-slate-100 text-slate-500 border border-slate-200'
                  }`}
                >
                  {isCompleted ? (
                    <Check className="w-4 h-4 stroke-[2.5]" />
                  ) : isBlocked ? (
                    <Lock className="w-3.5 h-3.5 text-rose-500" />
                  ) : (
                    <Icon className="w-4 h-4" />
                  )}

                  {/* Tiny step number pill */}
                  <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-navy-950 text-white text-[9px] flex items-center justify-center font-mono">
                    {s.step}
                  </span>
                </div>

                {/* Step Label */}
                <span
                  className={`text-[11px] font-semibold mt-1.5 transition-colors text-center ${
                    isCurrent
                      ? 'text-teal-700 font-bold'
                      : isCompleted
                      ? 'text-slate-800'
                      : isBlocked
                      ? 'text-rose-500'
                      : 'text-slate-400'
                  }`}
                >
                  {s.shortLabel}
                </span>

                {/* Status indicator note */}
                <span className="text-[9px] text-slate-400 hidden xl:block font-mono">
                  {isCompleted ? 'Done' : isCurrent ? 'Active' : isBlocked ? 'Blocked' : 'Next'}
                </span>
              </button>

              {/* Connecting Bar */}
              {index < SCREENING_STEPS_CONFIG.length - 1 && (
                <div
                  className={`flex-1 h-0.5 mx-1 transition-colors ${
                    status === 'completed'
                      ? 'bg-teal-500'
                      : isBlocked
                      ? 'bg-rose-200'
                      : 'bg-slate-200'
                  }`}
                />
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};
