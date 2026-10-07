import React from 'react';

export type MedicalStatusType =
  | 'GOOD'
  | 'BORDERLINE'
  | 'UNGRADABLE'
  | 'REFERABLE'
  | 'NON-REFERABLE'
  | 'PENDING REVIEW'
  | 'CONFIRMED'
  | 'MODIFIED'
  | 'LEVEL 0'
  | 'LEVEL 1'
  | 'LEVEL 2'
  | 'LEVEL 3'
  | 'LEVEL 4';

interface StatusBadgeProps {
  status: MedicalStatusType | string;
  size?: 'sm' | 'md' | 'lg';
  dot?: boolean;
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  size = 'md',
  dot = true,
  className = '',
}) => {
  const norm = status.toUpperCase().trim();

  let styles = 'bg-slate-100 text-slate-700 border-slate-200';
  let dotColor = 'bg-slate-400';

  if (norm === 'GOOD' || norm === 'NON-REFERABLE' || norm === 'CONFIRMED' || norm === 'LEVEL 0') {
    styles = 'bg-emerald-50 text-emerald-800 border-emerald-200/80';
    dotColor = 'bg-emerald-500';
  } else if (norm === 'BORDERLINE' || norm === 'LEVEL 1') {
    styles = 'bg-amber-50 text-amber-800 border-amber-200/80';
    dotColor = 'bg-amber-500';
  } else if (norm === 'REFERABLE' || norm === 'LEVEL 2') {
    styles = 'bg-orange-50 text-orange-800 border-orange-200/80';
    dotColor = 'bg-orange-500';
  } else if (norm === 'LEVEL 3') {
    styles = 'bg-rose-50 text-rose-800 border-rose-200/80';
    dotColor = 'bg-rose-600';
  } else if (norm === 'LEVEL 4') {
    styles = 'bg-purple-50 text-purple-900 border-purple-200/80 font-semibold';
    dotColor = 'bg-purple-600';
  } else if (norm === 'UNGRADABLE') {
    styles = 'bg-rose-100 text-rose-900 border-rose-300 font-semibold';
    dotColor = 'bg-rose-600 animate-pulse';
  } else if (norm === 'PENDING REVIEW' || norm === 'PENDING') {
    styles = 'bg-blue-50 text-blue-800 border-blue-200/80';
    dotColor = 'bg-blue-500';
  } else if (norm === 'MODIFIED') {
    styles = 'bg-indigo-50 text-indigo-800 border-indigo-200/80';
    dotColor = 'bg-indigo-500';
  }

  const sizes = {
    sm: 'text-[11px] px-2 py-0.5 gap-1.5',
    md: 'text-xs px-2.5 py-1 gap-1.5',
    lg: 'text-sm px-3 py-1.5 gap-2 font-medium',
  };

  return (
    <span
      className={`inline-flex items-center rounded-full border font-medium uppercase tracking-wider ${styles} ${sizes[size]} ${className}`}
    >
      {dot && <span className={`h-1.5 w-1.5 rounded-full ${dotColor}`} />}
      {status}
    </span>
  );
};
