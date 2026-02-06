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
import { DEMO_HEALTH_RESULT, DEMO_ANALYSIS_RESULT, DEMO_BAYESIAN_INSIGHTS, DEMO_MULTIVARIANT_HEALTH, DEMO_MULTIVARIANT_ANALYSIS, DEMO_MULTIVARIANT_BAYESIAN } from './data/demoData';

type PageType = 'analysis' | 'memo' | 'calculator';

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

    // Simple way to listen to localStorage changes from IntegrationConnect
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
        // Clear file upload specific usage if switching to integration
        setSelectedFile(null);
        setHealthResult(null); // Clear health result as it's not from CSV
      } catch (err) {
        console.warn('Auto-sync failed', err);
      }
    };

    if (isAutoSync && activeExperimentId && !loading) {
      intervalId = setInterval(performSync, 30000); // 30 seconds
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
    // Disable auto-sync if manual file upload happens
    setIsAutoSync(false);
    setActiveExperimentId(null);

    setLoading(true);
    setError(null);
    setSelectedFile(file);
    try {
      // 1. Health Check
      const health = await uploadHealthCheck(file);
      setHealthResult(health);

      if (health.result.overall_status === 'Blocked') {
        setError("Health Check Failed: " + (health.result.schema.issues.join(", ") || health.result.srm?.message));
        setLoading(false);
        return;
      }

      // 2. Auto Analyze (for MVP)
      const analysis = await analyzeData(file);
      setAnalysisResult(analysis);

      // 3. Continuous Metrics (optional)
      try {
        const continuous = await analyzeContinuousMetrics(file);
        setContinuousResults(continuous.continuous_results || []);
      } catch (err) {
        console.warn('Continuous metrics failed:', err);
      }

      // 4. Bayesian Analysis (optional)
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
      // Integration results don't have health check reports usually
      setHealthResult(null);
      setContinuousResults([]);
      setBayesianInsights(null);
    } catch (err: unknown) {
      console.error(err);
      const errObj = err as { response?: { data?: { detail?: string } } };
      setError(errObj.response?.data?.detail || "Failed to analyze experiment");
      setIsAutoSync(false); // Stop sync on error
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

  return (
    <div className="min-h-screen bg-app-bg text-white font-body">
      <main className="py-6 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          {/* Navigation */}
          {analysisResult && (
            <div className="sticky top-0 z-50 bg-app-bg/95 backdrop-blur-sm pb-4 mb-2" data-tour="nav-tabs">
              <div className="flex gap-3">
                <button
                  onClick={() => setCurrentPage('analysis')}
                  className={`px-4 py-2 rounded-xl font-medium transition-all ${currentPage === 'analysis'
                    ? 'bg-primary text-white shadow-lg shadow-primary/20'
                    : 'bg-white/5 text-white/70 hover:bg-white/10'
                    }`}
                >
                  Analysis
                </button>
                <button
                  onClick={() => setCurrentPage('memo')}
                  className={`px-4 py-2 rounded-xl font-medium transition-all ${currentPage === 'memo'
                    ? 'bg-primary text-white shadow-lg shadow-primary/20'
                    : 'bg-white/5 text-white/70 hover:bg-white/10'
                    }`}
                >
                  Decision Memo
                </button>
                <button
                  onClick={() => setCurrentPage('calculator')}
                  className={`px-4 py-2 rounded-xl font-medium transition-all ${currentPage === 'calculator'
                    ? 'bg-primary text-white shadow-lg shadow-primary/20'
                    : 'bg-white/5 text-white/70 hover:bg-white/10'
                    }`}
                >
                  Power Calculator
                </button>

                {isAutoSync && (
                  <span className="flex items-center gap-2 px-3 py-1 bg-green-500/10 text-green-400 rounded-lg text-sm border border-green-500/20 ml-2 animate-pulse">
                    <span className="w-2 h-2 rounded-full bg-green-500"></span>
                    Live Sync
                  </span>
                )}

                <button
                  onClick={handleReset}
                  className="ml-auto px-4 py-2 rounded-xl font-medium text-gray-400 hover:text-white hover:bg-white/10 transition-all"
                >
                  Reset
                </button>
              </div>
            </div>
          )}

          {!analysisResult && (
            <div data-tour="experiment-metadata">
              <ExperimentMetadata onMetadataChange={({ name }) => setExperimentName(name)} />
            </div>
          )}

          {/* Main Content */}
          <div className="mt-8">
            {!analysisResult ? (
              <div className="w-full max-w-2xl mx-auto flex flex-col items-center justify-center gap-8">
                <div className="text-center space-y-2">
                  <h1 className="text-3xl font-bold tracking-tight">New Experiment</h1>
                  <p className="text-gray-400">Import data from an integration or upload a CSV.</p>
                </div>

                {/* Welcome banner for first-time visitors */}
                {!tour.hasSeenTour && !tour.isActive && (
                  <div className="w-full p-4 rounded-xl bg-primary/10 border border-primary/30 text-center animate-in fade-in slide-in-from-bottom-2">
                    <p className="text-white font-medium mb-2">First time here?</p>
                    <p className="text-white/60 text-sm mb-3">Take a quick tour to learn how ExperimentOS works.</p>
                    <button
                      onClick={tour.startTour}
                      className="px-4 py-2 bg-primary hover:bg-primary/80 text-white text-sm font-medium rounded-lg transition-all shadow-lg shadow-primary/20"
                    >
                      Start Tour
                    </button>
                  </div>
                )}

                <div className="w-full space-y-8">
                  <IntegrationConnect />

                  {isConnected && (
                    <ExperimentSelector onSelectExperiment={handleIntegrationSelect} isLoading={loading} />
                  )}

                  <div className="relative">
                    <div className="absolute inset-0 flex items-center">
                      <span className="w-full border-t border-white/10" />
                    </div>
                    <div className="relative flex justify-center text-xs uppercase">
                      <span className="bg-app-bg px-2 text-gray-500">Or upload file</span>
                    </div>
                  </div>

                  <FileUpload onFileSelect={handleFileSelect} isUploading={loading} />

                  {/* Try Demo buttons */}
                  <div className="flex justify-center gap-3" data-tour="try-demo">
                    <button
                      onClick={handleLoadDemo}
                      className="px-5 py-2.5 text-sm font-medium text-white/70 hover:text-white bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 rounded-xl transition-all"
                    >
                      Try Demo Data
                    </button>
                    <button
                      onClick={handleLoadMultiVariantDemo}
                      className="px-5 py-2.5 text-sm font-medium text-purple-400/70 hover:text-purple-300 bg-purple-500/5 hover:bg-purple-500/10 border border-purple-500/10 hover:border-purple-500/20 rounded-xl transition-all"
                    >
                      Try Multi-Variant Demo
                    </button>
                  </div>
                </div>

                {error && (
                  <div className="p-4 rounded-lg bg-danger/10 border border-danger/30 text-danger w-full text-center animate-in fade-in slide-in-from-bottom-2">
                    {error}
                  </div>
                )}

                {healthResult && !analysisResult && !error && (
                  <div className="p-4 rounded-lg bg-blue-500/10 border border-blue-500/30 text-blue-400 w-full text-center">
                    Health Check Passed! Analyzing...
                  </div>
                )}
              </div>
            ) : (
              <>
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
              </>
            )}
          </div>
        </div>
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
