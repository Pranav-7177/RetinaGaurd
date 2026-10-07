import React from 'react';
import {
  LayoutDashboard,
  ScanEye,
  Users,
  ClipboardCheck,
  BarChart3,
  Settings,
  Eye,
  Activity,
  AlertCircle
} from 'lucide-react';

import { reviewService } from '../../services/reviewService';

interface SidebarProps {
  currentRoute: string;
  onNavigate: (route: string) => void;
  pendingReviewCount?: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentRoute,
  onNavigate,
  pendingReviewCount: initialCount,
}) => {
  const [actualPendingCount, setActualPendingCount] = React.useState<number>(initialCount ?? 0);

  React.useEffect(() => {
    const fetchPending = async () => {
      try {
        const queue = await reviewService.getReviewQueue('PENDING');
        setActualPendingCount(queue.length);
      } catch {
        // fallback
      }
    };
    fetchPending();
  }, [currentRoute]);

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, path: '/dashboard' },
    { id: 'screening', label: 'AI Screening', icon: ScanEye, path: '/screening', highlight: true },
    { id: 'patients', label: 'Patient Registry', icon: Users, path: '/patients' },
    { id: 'review', label: 'Clinical Review', icon: ClipboardCheck, path: '/review', badge: actualPendingCount },
    { id: 'analytics', label: 'Screening & Simulation', icon: BarChart3, path: '/analytics' },
    { id: 'settings', label: 'System & Models', icon: Settings, path: '/settings' },
  ];

  return (
    <aside className="w-64 bg-navy-950 text-slate-300 flex flex-col justify-between border-r border-navy-850 h-screen sticky top-0 flex-shrink-0 z-30">
      {/* Brand Header */}
      <div>
        <div
          onClick={() => onNavigate('landing')}
          className="h-16 flex items-center px-6 border-b border-navy-900 gap-3 cursor-pointer hover:bg-navy-900/40 transition-colors"
          title="Return to Home / Landing"
        >
          <div className="h-10 w-10 rounded-xl bg-navy-900/90 border border-teal-500/30 flex items-center justify-center p-1.5 shadow-md shadow-teal-950/40 group-hover:border-teal-500/60 transition-colors">
            <img
              src="/retinaguard-icon-dark.png"
              alt="RetinaGuard Logo"
              className="w-full h-full object-contain"
            />
          </div>
          <div>
            <div className="font-bold text-white tracking-tight text-base font-sans flex items-center gap-1.5">
              <span>Retina</span>
              <span className="text-teal-400 font-extrabold">Guard</span>
            </div>
            <div className="text-[10px] text-slate-400 font-medium tracking-wider uppercase">
              Tele-Retina AI Platform
            </div>
          </div>
        </div>

        {/* Navigation Section */}
        <div className="px-3 py-5">
          <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider px-3 mb-2">
            Screening Workflow
          </div>
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = currentRoute === item.id || (item.id === 'patients' && currentRoute.startsWith('patients/'));
              
              return (
                <button
                  key={item.id}
                  onClick={() => onNavigate(item.id)}
                  className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition-all ${
                    isActive
                      ? 'bg-teal-600 text-white font-semibold shadow-md shadow-teal-900/30'
                      : 'text-slate-400 hover:text-slate-100 hover:bg-navy-900'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                    <span>{item.label}</span>
                  </div>
                  {item.badge !== undefined && item.badge > 0 && (
                    <span
                      className={`px-1.5 py-0.5 rounded-full text-[10px] font-bold ${
                        isActive ? 'bg-white text-teal-800' : 'bg-amber-500 text-navy-950'
                      }`}
                    >
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Footer Info & Medical Disclaimer */}
      <div className="p-4 border-t border-navy-900 bg-navy-950/70 space-y-3">
        <div className="p-2.5 rounded-lg bg-navy-900/90 border border-slate-800/80">
          <div className="flex items-center gap-2 text-[11px] text-slate-300 font-medium">
            <Activity className="w-3.5 h-3.5 text-teal-400" />
            <span>Classifier: EfficientNet-B0</span>
          </div>
          <div className="text-[10px] text-slate-500 mt-1 font-mono">
            ICDR Grade (0–4) • Referral: ≥2
          </div>
        </div>

        <div className="flex items-start gap-1.5 text-[10px] text-slate-500 leading-tight">
          <AlertCircle className="w-3 h-3 text-slate-400 flex-shrink-0 mt-0.5" />
          <span>Research prototype. Decision support only.</span>
        </div>
      </div>
    </aside>
  );
};
