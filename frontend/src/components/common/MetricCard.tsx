import React from 'react';

interface MetricCardProps {
  label: string;
  value: string | number;
  subValue?: string;
  change?: string;
  isPositive?: boolean;
  icon?: React.ReactNode;
  badge?: React.ReactNode;
  variant?: 'default' | 'teal' | 'rose' | 'amber' | 'emerald';
  className?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  subValue,
  change,
  isPositive,
  icon,
  badge,
  variant = 'default',
  className = '',
}) => {
  const borderVariants = {
    default: 'border-slate-200/80 hover:border-slate-300',
    teal: 'border-teal-200/80 bg-gradient-to-br from-white to-teal-50/30',
    rose: 'border-rose-200/80 bg-gradient-to-br from-white to-rose-50/30',
    amber: 'border-amber-200/80 bg-gradient-to-br from-white to-amber-50/30',
    emerald: 'border-emerald-200/80 bg-gradient-to-br from-white to-emerald-50/30',
  };

  return (
    <div
      className={`bg-white rounded-xl border p-5 shadow-card-subtle transition-all duration-200 ${borderVariants[variant]} ${className}`}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">{label}</span>
        {icon && <div className="p-2 rounded-lg bg-slate-50 text-slate-600 border border-slate-100">{icon}</div>}
      </div>

      <div className="mt-2 flex items-baseline justify-between gap-2">
        <div className="text-2xl font-bold text-navy-950 tracking-tight font-sans">{value}</div>
        {badge && <div>{badge}</div>}
      </div>

      {(subValue || change) && (
        <div className="mt-2 flex items-center gap-2 text-xs text-slate-500">
          {change && (
            <span className={`font-semibold ${isPositive ? 'text-emerald-600' : 'text-rose-600'}`}>
              {change}
            </span>
          )}
          {subValue && <span>{subValue}</span>}
        </div>
      )}
    </div>
  );
};
