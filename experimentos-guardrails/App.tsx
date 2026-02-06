import React, { useState, useEffect, useCallback } from 'react';
import Dashboard from './components/Dashboard';
import { uploadHealthCheck, analyzeData, analyzeContinuousMetrics, analyzeBayesian, analyzeExperiment } from './api/client';
import type { HealthCheckResult, AnalysisResult, ContinuousMetricResult, BayesianInsightsUnion } from './api/client';
import { FileUpload } from './components/FileUpload';
import { ExperimentMetadata } from './components/ExperimentMetadata';
import { DecisionMemo } from './components/DecisionMemo';
import { PowerCalculator } from './components/PowerCalculator';
import { IntegrationConnect } from './components/IntegrationConnect';
import { ExperimentSelector } from './components/ExperimentSelector';
import TourOverlay from './components/TourOverlay';
import { useTour } from './hooks/useTour';
import Icon from './components/Icon';
import { DEMO_HEALTH_RESULT, DEMO_ANALYSIS_RESULT, DEMO_BAYESIAN_INSIGHTS, DEMO_MULTIVARIANT_HEALTH, DEMO_MULTIVARIANT_ANALYSIS, DEMO_MULTIVARIANT_BAYESIAN } from './data/demoData';

type PageType = 'analysis' | 'memo' | 'calculator';

const NAV_ITEMS: { id: PageType; label: string; icon: string }[] = [
  { id: 'analysis', label: 'Analysis', icon: 'analytics' },
  { id: 'memo', label: 'Memo', icon: 'description' },
  { id: 'calculator', label: 'Calculator', icon: 'calculate' },
];

const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<PageType>('analysis');
  const [experimentName, setExperimentName] = useState('Experiment');
  const [, setSelectedFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [healthResult, setHealthResult] = useState<HealthCheckResult | null>(null);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [continuousResults, setContinuousResults] = useState<ContinuousMetricResult[]>([]);
  const [bayesianInsights, setBayesianInsights] = useState<BayesianInsightsUnion | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Integration State
  const [isConnected, setIsConnected] = useState(false);
  const [activeExperimentId, setActiveExperimentId] = useState<string | null>(null);
  const [isAutoSync, setIsAutoSync] = useState(false);

  // Tour State
  const tour = useTour();

  // Check connection on mount and storage events
  useEffect(() => {
    const checkConnection = () => {
      const hasKey = !!localStorage.getItem('integration_api_key');
      setIsConnected(hasKey);
    };
    checkConnection();

    const interval = setInterval(checkConnection, 1000);
    return () => clearInterval(interval);
  }, []);

  // Polling for Auto-Sync
  useEffect(() => {
    let intervalId: ReturnType<typeof setInterval> | undefined;

    const performSync = async () => {
      if (!activeExperimentId || !isConnected) return;
      const provider = localStorage.getItem('integration_provider');
      if (!provider) return;

      console.log('Auto-syncing experiment:', activeExperimentId);
      try {
        const result = await analyzeExperiment(provider, activeExperimentId);
        setAnalysisResult(result);
        setExperimentName(result.experiment_id || 'Experiment');
        setSelectedFile(null);
        setHealthResult(null);
      } catch (err) {
        console.warn('Auto-sync failed', err);
      }
    };

    if (isAutoSync && activeExperimentId && !loading) {
      intervalId = setInterval(performSync, 30000);
    }

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [isAutoSync, activeExperimentId, isConnected, loading]);

  const handleLoadDemo = useCallback(() => {
    setHealthResult(DEMO_HEALTH_RESULT);
    setAnalysisResult(DEMO_ANALYSIS_RESULT);
    setBayesianInsights(DEMO_BAYESIAN_INSIGHTS);
    setContinuousResults([]);
    setExperimentName('Demo: Homepage Banner Test');
    setError(null);
    setSelectedFile(null);
    setIsAutoSync(false);
    setActiveExperimentId(null);
  }, []);

  const handleLoadMultiVariantDemo = useCallback(() => {
    setHealthResult(DEMO_MULTIVARIANT_HEALTH);
    setAnalysisResult(DEMO_MULTIVARIANT_ANALYSIS);
    setBayesianInsights(DEMO_MULTIVARIANT_BAYESIAN);
    setContinuousResults([]);
    setExperimentName('Demo: Multi-Variant Banner Test');
    setError(null);
    setSelectedFile(null);
    setIsAutoSync(false);
    setActiveExperimentId(null);
  }, []);

  const handleTourAction = useCallback((action: string) => {
    if (action === 'load-demo') {
      handleLoadDemo();
    }
  }, [handleLoadDemo]);

  const handleFileSelect = async (file: File) => {
    setIsAutoSync(false);
    setActiveExperimentId(null);

    setLoading(true);
    setError(null);
    setSelectedFile(file);
    try {
      const health = await uploadHealthCheck(file);
      setHealthResult(health);

      if (health.result.overall_status === 'Blocked') {
        setError("Health Check Failed: " + (health.result.schema.issues.join(", ") || health.result.srm?.message));
        setLoading(false);
        return;
      }

      const analysis = await analyzeData(file);
      setAnalysisResult(analysis);

      try {
        const continuous = await analyzeContinuousMetrics(file);
        setContinuousResults(continuous.continuous_results || []);
      } catch (err) {
        console.warn('Continuous metrics failed:', err);
      }

      try {
        const bayesian = await analyzeBayesian(file);
        setBayesianInsights(bayesian.bayesian_insights);
      } catch (err) {
        console.warn('Bayesian analysis failed:', err);
      }

    } catch (err: unknown) {
      console.error(err);
      const errObj = err as { response?: { data?: { detail?: string } }; message?: string };
      setError(errObj.response?.data?.detail || errObj.message || "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  const handleIntegrationSelect = async (experimentId: string, autoSync: boolean) => {
    setLoading(true);
    setError(null);
    setIsAutoSync(autoSync);
    setActiveExperimentId(experimentId);

    const provider = localStorage.getItem('integration_provider');
    if (!provider) return;

    try {
      const result = await analyzeExperiment(provider, experimentId);
      setAnalysisResult(result);
      setExperimentName(result.experiment_id || 'Experiment');
      setHealthResult(null);
      setContinuousResults([]);
      setBayesianInsights(null);
    } catch (err: unknown) {
      console.error(err);
      const errObj = err as { response?: { data?: { detail?: string } } };
      setError(errObj.response?.data?.detail || "Failed to analyze experiment");
      setIsAutoSync(false);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setCurrentPage('analysis');
    setExperimentName('Experiment');
    setSelectedFile(null);
    setHealthResult(null);
    setAnalysisResult(null);
    setContinuousResults([]);
    setBayesianInsights(null);
    setError(null);
    setActiveExperimentId(null);
    setIsAutoSync(false);
  };

  const hasResults = !!analysisResult;

  return (
    <div className="h-screen flex flex-col bg-app-bg text-white font-body overflow-hidden">
      {/* Top bar */}
      <header className="flex items-center justify-between h-14 px-5 border-b border-white/[0.06] bg-surface-0/80 backdrop-blur-xl shrink-0 z-30">
        <div className="flex items-center gap-3 cursor-pointer group" onClick={handleReset}>
          <div className="w-8 h-8 rounded-lg bg-primary/15 flex items-center justify-center">
            <Icon name="science" className="text-primary" size={18} />
          </div>
          <span className="text-[15px] font-bold tracking-tight text-white group-hover:text-primary transition-colors">
            ExperimentOS
          </span>
          <span className="hidden sm:inline text-[10px] font-mono text-white/25 bg-white/[0.04] px-1.5 py-0.5 rounded border border-white/[0.04]">
            v2.4
          </span>
        </div>

        {hasResults && (
          <nav className="flex items-center gap-1" data-tour="nav-tabs">
            {NAV_ITEMS.map((item) => (
              <button
                key={item.id}
                onClick={() => setCurrentPage(item.id)}
                className={`focus-ring flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all ${
                  currentPage === item.id
                    ? 'bg-primary/15 text-primary'
                    : 'text-white/50 hover:text-white/80 hover:bg-white/[0.04]'
                }`}
              >
                <Icon name={item.icon} size={16} className={currentPage === item.id ? 'text-primary' : 'text-white/40'} />
                <span className="hidden sm:inline">{item.label}</span>
              </button>
            ))}

            {isAutoSync && (
              <span className="flex items-center gap-1.5 px-2.5 py-1 bg-primary/10 text-primary rounded-lg text-xs font-medium border border-primary/15 ml-2">
                <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse-dot" />
                Live
              </span>
            )}
          </nav>
        )}

        <div className="flex items-center gap-2">
          {hasResults && (
            <button
              onClick={handleReset}
              className="focus-ring flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm text-white/40 hover:text-white/70 hover:bg-white/[0.04] transition-all"
            >
              <Icon name="restart_alt" size={16} />
              <span className="hidden sm:inline">New</span>
            </button>
          )}
        </div>
      </header>

      {/* Main content area */}
      <main className="flex-1 overflow-hidden">
        {!hasResults ? (
          /* ── Landing / Upload State ── */
          <div className="h-full overflow-y-auto custom-scrollbar">
            <div className="max-w-2xl mx-auto px-5 py-12 flex flex-col items-center gap-8">

              {/* Hero */}
              <div className="text-center space-y-3" data-tour="experiment-metadata">
                <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary/10 border border-primary/15 text-primary text-xs font-medium mb-2">
                  <Icon name="science" size={14} />
                  A/B Test Decision Engine
                </div>
                <h1 className="text-3xl sm:text-4xl font-bold tracking-tight bg-gradient-to-b from-white to-white/60 bg-clip-text text-transparent">
                  New Experiment
                </h1>
                <p className="text-white/40 text-sm max-w-md mx-auto leading-relaxed">
                  Import data from an integration or upload a CSV to get started with your analysis.
                </p>
              </div>

              {/* Experiment metadata */}
              <div className="w-full">
                <ExperimentMetadata onMetadataChange={({ name }) => setExperimentName(name)} />
              </div>

              {/* Welcome banner for first-time visitors */}
              {!tour.hasSeenTour && !tour.isActive && (
                <div className="w-full glass-card p-5 text-center">
                  <p className="text-white font-medium mb-1.5">First time here?</p>
                  <p className="text-white/40 text-sm mb-4">Take a quick tour to learn how ExperimentOS works.</p>
                  <div className="flex items-center justify-center gap-3">
                    <button
                      onClick={tour.startTour}
                      className="btn-primary text-sm"
                    >
                      Start Tour
                    </button>
                    <button
                      onClick={tour.skipTour}
                      className="btn-ghost text-sm"
                    >
                      Skip
                    </button>
                  </div>
                </div>
              )}

              {/* Integration */}
              <div className="w-full space-y-6">
                <IntegrationConnect />

                {isConnected && (
                  <ExperimentSelector onSelectExperiment={handleIntegrationSelect} isLoading={loading} />
                )}

                <div className="relative">
                  <div className="absolute inset-0 flex items-center">
                    <span className="w-full border-t border-white/[0.06]" />
                  </div>
                  <div className="relative flex justify-center">
                    <span className="bg-app-bg px-3 text-[11px] font-mono uppercase tracking-widest text-white/25">
                      Or upload file
                    </span>
                  </div>
                </div>

                <FileUpload onFileSelect={handleFileSelect} isUploading={loading} />

                {/* Try Demo buttons */}
                <div className="flex flex-col sm:flex-row justify-center gap-3" data-tour="try-demo">
                  <button
                    onClick={handleLoadDemo}
                    className="btn-ghost text-sm flex items-center justify-center gap-2"
                  >
                    <Icon name="play_circle" size={16} className="text-white/40" />
                    Try Demo Data
                  </button>
                  <button
                    onClick={handleLoadMultiVariantDemo}
                    className="px-4 py-2 text-sm font-medium text-purple-400/80 hover:text-purple-300 bg-purple-500/[0.06] hover:bg-purple-500/10 border border-purple-500/10 hover:border-purple-500/20 rounded-xl transition-all flex items-center justify-center gap-2"
                  >
                    <Icon name="hub" size={16} className="text-purple-400/60" />
                    Multi-Variant Demo
                  </button>
                </div>
              </div>

              {error && (
                <div className="w-full p-4 rounded-xl bg-danger/10 border border-danger/20 text-danger text-sm text-center">
                  {error}
                </div>
              )}

              {healthResult && !analysisResult && !error && (
                <div className="w-full p-4 rounded-xl bg-info/10 border border-info/20 text-info text-sm text-center flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-info/30 border-t-info rounded-full animate-spin" />
                  Health Check Passed. Analyzing...
                </div>
              )}
            </div>
          </div>
        ) : (
          /* ── Results State ── */
          <div className="h-full overflow-y-auto custom-scrollbar">
            {currentPage === 'analysis' && (
              <Dashboard
                data={analysisResult}
                health={healthResult}
                continuousResults={continuousResults}
                bayesianInsights={bayesianInsights}
              />
            )}
            {currentPage === 'memo' && (
              <DecisionMemo
                experimentName={experimentName}
                health={healthResult}
                analysisResult={analysisResult}
                bayesianInsights={bayesianInsights}
              />
            )}
            {currentPage === 'calculator' && <PowerCalculator />}
          </div>
        )}
      </main>

      {/* Tour Overlay */}
      {tour.isActive && tour.currentStep && (
        <TourOverlay
          step={tour.currentStep}
          currentIndex={tour.currentIndex}
          totalSteps={tour.totalSteps}
          onNext={tour.nextStep}
          onPrev={tour.prevStep}
          onSkip={tour.skipTour}
          onAction={handleTourAction}
        />
      )}
    </div>
  );
};

export default App;
