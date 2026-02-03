import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';
import { FileUpload } from './components/FileUpload';
import { uploadHealthCheck, analyzeData, analyzeContinuousMetrics, analyzeBayesian, HealthCheckResult, AnalysisResult, ContinuousMetricResult, BayesianInsights } from './api/client';

const App: React.FC = () => {
  const [isUploading, setIsUploading] = useState(false);
  const [healthResult, setHealthResult] = useState<HealthCheckResult | null>(null);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [continuousResults, setContinuousResults] = useState<ContinuousMetricResult[]>([]);
  const [bayesianInsights, setBayesianInsights] = useState<BayesianInsights | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileSelect = async (file: File) => {
    setIsUploading(true);
    setError(null);
    try {
      // 1. Health Check
      const health = await uploadHealthCheck(file);
      setHealthResult(health);

      if (health.result.overall_status === 'Blocked') {
        setError("Health Check Failed: " + (health.result.schema.issues.join(", ") || health.result.srm?.message));
        setIsUploading(false);
        return;
      }

      // 2. Auto Analyze (for MVP)
      // In a real app, we might want to let user review health check first
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

    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || err.message || "An error occurred");
    } finally {
      setIsUploading(false);
    }
  };

  const handleReset = () => {
    setHealthResult(null);
    setAnalysisResult(null);
    setContinuousResults([]);
    setBayesianInsights(null);
    setError(null);
  };

  return (
    <div className="flex h-screen w-full bg-background-dark text-white font-display overflow-hidden selection:bg-primary/30">
      <Sidebar onReset={handleReset} />
      <main className="flex-1 flex flex-col h-full overflow-hidden relative">
        {/* Background Decorative Gradients */}
        <div className="absolute top-0 right-0 w-[800px] h-[500px] bg-primary/5 rounded-full blur-[120px] pointer-events-none z-0"></div>
        <div className="absolute bottom-0 left-0 w-[600px] h-[400px] bg-blue-500/5 rounded-full blur-[120px] pointer-events-none z-0"></div>

        {/* Main Content */}
        <div className="z-10 h-full flex flex-col relative p-6 overflow-y-auto">
          {/* Header / Title if needed */}

          {!analysisResult ? (
            <div className="flex flex-col items-center justify-center h-full max-w-2xl mx-auto w-full gap-8">
              <div className="text-center space-y-2">
                <h1 className="text-3xl font-bold tracking-tight">New Experiment</h1>
                <p className="text-gray-400">Upload your experiment data (CSV) to get started.</p>
              </div>

              <FileUpload onFileSelect={handleFileSelect} isUploading={isUploading} />

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
            <Dashboard data={analysisResult} health={healthResult} />
          )}
        </div>
      </main>
    </div>
  );
};

export default App;