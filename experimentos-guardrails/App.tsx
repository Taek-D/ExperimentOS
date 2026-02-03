import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';
import { uploadHealthCheck, analyzeData, analyzeContinuousMetrics, analyzeBayesian } from './api/client';
import type { HealthCheckResult, AnalysisResult, ContinuousMetricResult, BayesianInsights } from './api/client';
import { FileUpload } from './components/FileUpload';
import { ExperimentMetadata } from './components/ExperimentMetadata';
import { DecisionMemo } from './components/DecisionMemo';
import { PowerCalculator } from './components/PowerCalculator';

type PageType = 'analysis' | 'memo' | 'calculator';

const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<PageType>('analysis');
  const [experimentName, setExperimentName] = useState('Experiment');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [healthResult, setHealthResult] = useState<HealthCheckResult | null>(null);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [continuousResults, setContinuousResults] = useState<ContinuousMetricResult[]>([]);
  const [bayesianInsights, setBayesianInsights] = useState<BayesianInsights | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileSelect = async (file: File) => {
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
  };

  return (
    <div className="min-h-screen bg-app-bg text-white font-body">
      <main className="py-6 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          {/* Navigation */}
          {analysisResult && (
            <div className="flex gap-3 mb-6">
              <button
                onClick={() => setCurrentPage('analysis')}
                className={`px-4 py-2 rounded-xl font-medium transition-all ${currentPage === 'analysis'
                  ? 'bg-primary text-white shadow-lg shadow-primary/20'
                  : 'bg-white/5 text-white/70 hover:bg-white/10'
                  }`}
              >
                📊 Analysis
              </button>
              <button
                onClick={() => setCurrentPage('memo')}
                className={`px-4 py-2 rounded-xl font-medium transition-all ${currentPage === 'memo'
                  ? 'bg-primary text-white shadow-lg shadow-primary/20'
                  : 'bg-white/5 text-white/70 hover:bg-white/10'
                  }`}
              >
                📝 Decision Memo
              </button>
              <button
                onClick={() => setCurrentPage('calculator')}
                className={`px-4 py-2 rounded-xl font-medium transition-all ${currentPage === 'calculator'
                  ? 'bg-primary text-white shadow-lg shadow-primary/20'
                  : 'bg-white/5 text-white/70 hover:bg-white/10'
                  }`}
              >
                🔢 Power Calculator
              </button>
            </div>
          )}

          {!analysisResult && <ExperimentMetadata onNameChange={setExperimentName} />}

          {/* Main Content */}
          <div className="mt-8">
            {!analysisResult ? (
              <div className="w-full max-w-2xl mx-auto flex flex-col items-center justify-center gap-8">
                <div className="text-center space-y-2">
                  <h1 className="text-3xl font-bold tracking-tight">New Experiment</h1>
                  <p className="text-gray-400">Upload your experiment data (CSV) to get started.</p>
                </div>

                <FileUpload onFileSelect={handleFileSelect} isUploading={loading} />

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
    </div>
  );
};

export default App;