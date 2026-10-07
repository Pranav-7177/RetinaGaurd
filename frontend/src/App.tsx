import React, { useState, useEffect } from 'react';
import { AppShell } from './components/layout/AppShell';
import { LandingPage } from './pages/LandingPage';
import { DashboardPage } from './pages/DashboardPage';
import { ScreeningPage } from './pages/ScreeningPage';
import { PatientsPage } from './pages/PatientsPage';
import { PatientDetailPage } from './pages/PatientDetailPage';
import { ReviewQueuePage } from './pages/ReviewQueuePage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { SettingsPage } from './pages/SettingsPage';

export function App() {
  const getInitialRoute = (): string => {
    if (typeof window === 'undefined') return 'landing';
    const path = window.location.pathname.replace(/^\/+/, '');
    if (!path || path === 'landing') return 'landing';
    return path;
  };

  const [currentRoute, setCurrentRoute] = useState<string>(getInitialRoute);
  const [selectedPatientId, setSelectedPatientId] = useState<string | null>(null);

  useEffect(() => {
    const handlePopState = () => {
      const path = window.location.pathname.replace(/^\/+/, '');
      setCurrentRoute(path || 'landing');
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const handleNavigate = (route: string) => {
    setCurrentRoute(route);
    const targetPath = route === 'landing' || route === '/' ? '/' : `/${route}`;
    if (window.location.pathname !== targetPath) {
      window.history.pushState(null, '', targetPath);
    }
    window.scrollTo(0, 0);
  };

  const handleOpenPatientProfile = (patientId: string) => {
    setSelectedPatientId(patientId);
    handleNavigate('patients/detail');
  };

  const handleStartScreeningForPatient = (patientId: string) => {
    setSelectedPatientId(patientId);
    handleNavigate('screening');
  };

  // If user is on the landing page, render it outside the clinical AppShell
  if (currentRoute === 'landing' || currentRoute === '/') {
    return (
      <LandingPage
        onStartScreening={() => handleNavigate('dashboard')}
        onNavigate={handleNavigate}
      />
    );
  }

  // Clinical workspace routes wrapped in AppShell
  return (
    <AppShell currentRoute={currentRoute} onNavigate={handleNavigate}>
      {currentRoute === 'dashboard' && (
        <DashboardPage
          onNavigate={handleNavigate}
          onOpenScreeningSession={() => handleNavigate('screening')}
        />
      )}

      {currentRoute === 'screening' && (
        <ScreeningPage onReturnToDashboard={() => handleNavigate('dashboard')} />
      )}

      {currentRoute === 'patients' && (
        <PatientsPage
          onSelectPatient={handleOpenPatientProfile}
          onNewScreeningForPatient={handleStartScreeningForPatient}
        />
      )}

      {currentRoute === 'patients/detail' && selectedPatientId && (
        <PatientDetailPage
          patientId={selectedPatientId}
          onBack={() => handleNavigate('patients')}
          onStartScreening={handleStartScreeningForPatient}
        />
      )}

      {currentRoute === 'review' && (
        <ReviewQueuePage
          onOpenScreeningWorkspace={() => handleNavigate('screening')}
        />
      )}

      {currentRoute === 'analytics' && <AnalyticsPage />}

      {currentRoute === 'settings' && <SettingsPage />}

      {/* Fallback for unmatched route inside app */}
      {![
        'dashboard',
        'screening',
        'patients',
        'patients/detail',
        'review',
        'analytics',
        'settings',
      ].includes(currentRoute) && (
        <DashboardPage
          onNavigate={handleNavigate}
          onOpenScreeningSession={() => handleNavigate('screening')}
        />
      )}
    </AppShell>
  );
}

export default App;
