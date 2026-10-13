import React, { useState, useEffect } from 'react';
import { api } from './api/client';
import { useLiveEvents } from './hooks/useLiveEvents';
import { Navbar } from './components/Navbar';
import { Sidebar, TabType } from './components/Sidebar';
import { DemoControlsModal } from './components/DemoControlsModal';
import { OverviewPage } from './pages/OverviewPage';
import { ReleaseExplorerPage } from './pages/ReleaseExplorerPage';
import { ReleaseDetailsPage } from './pages/ReleaseDetailsPage';
import { LiveEventMonitorPage } from './pages/LiveEventMonitorPage';
import { AIExplanationPage } from './pages/AIExplanationPage';
import { AuditHistoryPage } from './pages/AuditHistoryPage';
import { SecuritySettingsPage } from './pages/SecuritySettingsPage';
import { DashboardSummary, Release, Project, AssessmentRecord } from './types';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<TabType>('overview');
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [releases, setReleases] = useState<Release[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedReleaseId, setSelectedReleaseId] = useState<string>('rel-payment-1.0.0');
  const [currentAssessment, setCurrentAssessment] = useState<AssessmentRecord | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [isDemoModalOpen, setIsDemoModalOpen] = useState<boolean>(false);

  const refreshData = async () => {
    try {
      const [sum, relList, projList] = await Promise.all([
        api.getDashboardSummary(),
        api.getReleases(),
        api.getProjects()
      ]);
      setSummary(sum);
      setReleases(relList);
      setProjects(projList);

      if (relList.length > 0 && !selectedReleaseId) {
        setSelectedReleaseId(relList[0].release_id);
      }

      if (selectedReleaseId) {
        const asm = await api.getLatestAssessment(selectedReleaseId).catch(() => null);
        setCurrentAssessment(asm);
      }
    } catch (err) {
      console.error('Error refreshing dashboard data', err);
    } finally {
      setLoading(false);
    }
  };

  // Live SSE stream with automatic data update
  const { 
    status: connectionStatus, 
    events,
    isPaused,
    togglePause,
    reconnect,
    clearEvents,
    lastReceivedAt,
    errorMessage 
  } = useLiveEvents((event) => {
    // Whenever an event arrives via SSE, refresh dashboard metrics in the background!
    refreshData();
  });

  useEffect(() => {
    refreshData();
  }, [selectedReleaseId]);

  const handleSelectRelease = (releaseId: string) => {
    setSelectedReleaseId(releaseId);
    setCurrentTab('details');
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Navbar
        connectionStatus={connectionStatus}
        onOpenDemoModal={() => setIsDemoModalOpen(true)}
        onSelectTab={(tab) => setCurrentTab(tab)}
        currentTab={currentTab}
      />

      <div className="flex-1 flex overflow-hidden">
        <Sidebar
          currentTab={currentTab}
          onSelectTab={(tab) => setCurrentTab(tab)}
          releases={releases}
        />

        <main className="flex-1 overflow-y-auto p-6 md:p-8 bg-gradient-to-b from-slate-900/20 to-slate-950">
          <div className="max-w-7xl mx-auto">
            {currentTab === 'overview' && (
              <OverviewPage
                summary={summary}
                loading={loading}
                onSelectRelease={handleSelectRelease}
                onNavigateExplorer={() => setCurrentTab('explorer')}
              />
            )}

            {currentTab === 'explorer' && (
              <ReleaseExplorerPage
                releases={releases}
                onSelectRelease={handleSelectRelease}
              />
            )}

            {currentTab === 'details' && (
              <ReleaseDetailsPage
                releaseId={selectedReleaseId}
                releases={releases}
                onSelectRelease={(id) => setSelectedReleaseId(id)}
                onOpenDemoModal={() => setIsDemoModalOpen(true)}
              />
            )}

            {currentTab === 'events' && (
              <LiveEventMonitorPage
                events={events}
                connectionStatus={connectionStatus}
                isPaused={isPaused}
                onTogglePause={togglePause}
                onReconnect={reconnect}
                onClearEvents={clearEvents}
                lastReceivedAt={lastReceivedAt}
                errorMessage={errorMessage}
                onOpenDemoModal={() => setIsDemoModalOpen(true)}
              />
            )}

            {currentTab === 'ai' && (
              <AIExplanationPage
                releases={releases}
                selectedReleaseId={selectedReleaseId}
                onSelectRelease={(id) => setSelectedReleaseId(id)}
                assessment={currentAssessment}
              />
            )}

            {currentTab === 'audit' && (
              <AuditHistoryPage
                initialEvents={summary?.recent_events || []}
              />
            )}

            {currentTab === 'settings' && (
              <SecuritySettingsPage
                projects={projects}
                onProjectUpdated={refreshData}
              />
            )}
          </div>
        </main>
      </div>

      <DemoControlsModal
        isOpen={isDemoModalOpen}
        onClose={() => setIsDemoModalOpen(false)}
        onTriggered={refreshData}
        currentReleaseId={selectedReleaseId}
      />
    </div>
  );
};
