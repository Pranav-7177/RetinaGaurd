import React from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';

interface AppShellProps {
  currentRoute: string;
  onNavigate: (route: string) => void;
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({
  currentRoute,
  onNavigate,
  children,
}) => {
  const routeTitles: Record<string, string> = {
    dashboard: 'Command Center & Screening Overview',
    screening: 'AI-Assisted Retinal Screening Workspace',
    patients: 'Patient Registry & Longitudinal History',
    review: 'Clinical Review & Ophthalmologist Triage',
    analytics: 'Epidemiology, Model Benchmarks & Capacity Simulation',
    settings: 'Telemedicine Settings & Model Specifications',
  };

  const currentTitle = routeTitles[currentRoute.split('/')[0]] || 'Screening Workspace';

  return (
    <div className="flex h-screen w-full bg-slate-50 overflow-hidden">
      <Sidebar currentRoute={currentRoute} onNavigate={onNavigate} />
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        <Header currentRouteName={currentTitle} />
        <main className="flex-1 overflow-y-auto p-6 md:p-8 bg-slate-50/50">
          <div className="max-w-7xl mx-auto">{children}</div>
        </main>
      </div>
    </div>
  );
};
