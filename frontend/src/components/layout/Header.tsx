import React, { useState, useEffect } from 'react';
import { Activity, ShieldAlert, Wifi, Server, Stethoscope, ChevronRight, User } from 'lucide-react';
import { Badge } from '../common/Badge';

interface HeaderProps {
  currentRouteName: string;
}

export const Header: React.FC<HeaderProps> = ({ currentRouteName }) => {
  const [apiStatus, setApiStatus] = useState<'connected' | 'checking' | 'offline'>('checking');

  useEffect(() => {
    const checkApi = async () => {
      try {
        const res = await fetch('/api/v1/health');
        if (res.ok) setApiStatus('connected');
        else setApiStatus('offline');
      } catch {
        setApiStatus('offline');
      }
    };
    checkApi();
    const interval = setInterval(checkApi, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="h-16 bg-white border-b border-slate-200/80 px-6 flex items-center justify-between z-20">
      {/* Route Breadcrumb & Telemedicine Hub info */}
      <div className="flex items-center gap-3">
        <div className="flex items-center text-xs text-slate-500 font-medium">
          <img src="/retinaguard-icon.png" alt="" className="h-4 w-auto object-contain mr-1.5 opacity-80" />
          <span>Tele-Retina Network</span>
          <ChevronRight className="w-3.5 h-3.5 mx-1 text-slate-400" />
          <span className="text-navy-950 font-semibold text-sm">{currentRouteName}</span>
        </div>

        <div className="hidden lg:flex items-center ml-4 pl-4 border-l border-slate-200">
          <Badge variant="neutral" size="sm" className="text-slate-600 bg-slate-100">
            Hub: District Primary Care (Zone 4)
          </Badge>
        </div>
      </div>

      {/* Right Tools & Status Indicators */}
      <div className="flex items-center gap-4">
        {/* Research Prototype Warning Pill */}
        <div className="hidden md:flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-50 border border-amber-200/80 text-[11px] font-medium text-amber-900">
          <ShieldAlert className="w-3.5 h-3.5 text-amber-600" />
          <span>Research Prototype • Human Review Mandated</span>
        </div>

        {/* Backend Connectivity Status */}
        <div className="flex items-center gap-2 px-3 py-1 rounded-lg bg-slate-50 border border-slate-200 text-xs font-mono">
          <Server className="w-3.5 h-3.5 text-slate-500" />
          <span className="text-slate-600">FastAPI:</span>
          {apiStatus === 'connected' ? (
            <span className="flex items-center gap-1 text-emerald-700 font-semibold">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" /> Live
            </span>
          ) : apiStatus === 'checking' ? (
            <span className="text-slate-400">Syncing...</span>
          ) : (
            <span className="flex items-center gap-1 text-amber-700 font-medium">
              <span className="h-2 w-2 rounded-full bg-amber-500" /> Mock Client
            </span>
          )}
        </div>

        {/* Doctor / Reviewer Profile */}
        <div className="flex items-center gap-2 pl-3 border-l border-slate-200">
          <div className="w-8 h-8 rounded-full bg-navy-900 text-teal-400 flex items-center justify-center font-bold text-xs border border-navy-800">
            DR
          </div>
          <div className="hidden xl:block text-left">
            <div className="text-xs font-semibold text-navy-950">Dr. S. K. Venkat</div>
            <div className="text-[10px] text-slate-500">Tele-Ophthalmologist</div>
          </div>
        </div>
      </div>
    </header>
  );
};
