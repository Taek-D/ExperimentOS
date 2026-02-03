import React, { useState } from 'react';
import StatsCard from './StatsCard';
import MetricsTable from './MetricsTable';
import Icon from './Icon';
import { AnalysisResult, HealthCheckResult, ContinuousMetricResult, BayesianInsights } from '../api/client';
import { ContinuousMetrics } from './ContinuousMetrics';
import { BayesianInsightsComponent } from './BayesianInsights';

interface DashboardProps {
  data: AnalysisResult;
  health: HealthCheckResult | null;
  continuousResults?: ContinuousMetricResult[];
  bayesianInsights?: BayesianInsights | null;
}

type TabType = 'primary' | 'guardrails' | 'continuous' | 'bayesian';

const Dashboard: React.FC<DashboardProps> = ({ data, health, continuousResults = [], bayesianInsights = null }) => {
  const [activeTab, setActiveTab] = useState<TabType>('primary');
  const primary = data.primary_result;
  const guardrails = data.guardrail_results;

  // Derive stats
  const totalGuardrails = guardrails.length;
  const severeGuardrails = guardrails.filter((g: any) => g.severe).length;

  const liftPercentage = (primary.relative_lift * 100).toFixed(2);
  const isPositive = primary.relative_lift > 0;
  const pValue = primary.p_value.toFixed(4);
  const isSignificant = primary.is_significant;

  const tabs = [
    { id: 'primary' as TabType, label: 'Primary', icon: '📊' },
    { id: 'guardrails' as TabType, label: 'Guardrails', icon: '🛡️' },
    { id: 'continuous' as TabType, label: 'Continuous', icon: '📈', badge: continuousResults.length },
    { id: 'bayesian' as TabType, label: 'Bayesian', icon: 'ℹ️' },
  ];

  return (
    <>
      <header className="flex flex-col gap-6 p-6 pb-4 shrink-0 z-10">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex flex-col gap-1">
            <div className="flex items-center gap-3">
              <h2 className="text-white text-3xl font-bold tracking-tight font-display drop-shadow-sm">Experiment Results</h2>
              <span className="px-2 py-0.5 rounded-lg text-[10px] font-bold font-mono bg-primary/20 text-primary uppercase border border-primary/20 tracking-wider backdrop-blur-sm shadow-glow-primary">
                Analysis Complete
              </span>
            </div>
            <div className="flex items-center gap-3 text-white/60 text-sm font-mono mt-1">
              <span className="hover:text-white transition-colors cursor-pointer bg-white/5 px-2 py-0.5 rounded border border-white/5">
                {health?.filename || "data.csv"}
              </span>
              <span className="w-1 h-1 rounded-full bg-white/30"></span>
              <span>N={primary.control.users + primary.treatment.users}</span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <StatsCard
            title="Primary Lift"
            value={`${isPositive ? '+' : ''}${liftPercentage}%`}
            icon={isPositive ? "trending_up" : "trending_down"}
            subValue={
              <span className={`text-xs font-mono font-medium mb-1 px-1.5 py-0.5 rounded border ${isSignificant ? 'bg-primary/10 text-primary border-primary/10' : 'bg-white/5 text-white/50 border-white/5'}`}>
                {isSignificant ? 'Significant' : 'Not Significant'}
              </span>
            }
          />
          <StatsCard
            title="P-Value"
            value={pValue}
            icon="query_stats"
            subValue={<span className="text-primary text-xs font-mono font-medium mb-1">95% CI</span>}
          />
          <StatsCard
            title="Guardrails"
            value={`${totalGuardrails}`}
            icon="shield"
            variant={severeGuardrails > 0 ? "danger" : "default"}
            subValue={
              severeGuardrails > 0 ? (
                <span className="text-danger text-xs font-mono font-medium mb-1 bg-danger/10 px-1.5 py-0.5 rounded border border-danger/20">
                  {severeGuardrails} Severe
                </span>
              ) : (
                <span className="text-primary text-xs font-mono font-medium mb-1 bg-primary/10 px-1.5 py-0.5 rounded border border-primary/10">
                  All Healthy
                </span>
              )
            }
          />
        </div>
      </header>

      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="flex gap-2 px-6 pb-4 border-b border-white/10">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 rounded-lg font-medium transition-all flex items-center gap-2 ${activeTab === tab.id
                  ? 'bg-primary text-white shadow-lg shadow-primary/20'
                  : 'bg-white/5 text-white/70 hover:bg-white/10 hover:text-white'
                }`}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
              {tab.badge !== undefined && tab.badge > 0 && (
                <span className="ml-1 px-2 py-0.5 rounded-full bg-white/20 text-xs font-mono">{tab.badge}</span>
              )}
            </button>
          ))}
        </div>

        <div className="flex-1 overflow-auto p-6">
          {activeTab === 'primary' && <MetricsTable data={data} />}
          {activeTab === 'guardrails' && (
            <div className="space-y-4">
              <h3 className="text-xl font-semibold text-white mb-4">Guardrail Metrics</h3>
              {guardrails.length === 0 ? (
                <div className="text-center py-12 text-white/50"><p>No guardrails specified</p></div>
              ) : (
                <div className="space-y-3">
                  {guardrails.map((g: any, idx: number) => (
                    <div key={idx} className="p-6 bg-white/5 border border-white/10 rounded-2xl backdrop-blur-xl">
                      <div className="flex items-center justify-between mb-4">
                        <h4 className="text-lg font-semibold text-white">{g.name}</h4>
                        <span className={`px-3 py-1 rounded-lg text-sm font-medium ${g.severe ? 'bg-danger/20 text-danger border border-danger/30' :
                            g.worsened ? 'bg-orange-500/20 text-orange-400 border border-orange-500/30' :
                              'bg-primary/20 text-primary border border-primary/30'
                          }`}>
                          {g.severe ? '🚫 Severe' : g.worsened ? '⚠️ Worsened' : '✅ OK'}
                        </span>
                      </div>
                      <div className="grid grid-cols-3 gap-4">
                        <div>
                          <div className="text-white/50 text-xs mb-1">Control</div>
                          <div className="text-white text-lg font-medium">{(g.control_rate * 100).toFixed(2)}%</div>
                        </div>
                        <div>
                          <div className="text-white/50 text-xs mb-1">Treatment</div>
                          <div className="text-white text-lg font-medium">{(g.treatment_rate * 100).toFixed(2)}%</div>
                        </div>
                        <div>
                          <div className="text-white/50 text-xs mb-1">Delta</div>
                          <div className={`text-lg font-medium ${g.delta > 0 ? 'text-green-400' : 'text-red-400'}`}>
                            {(g.delta * 100).toFixed(2)}%
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
          {activeTab === 'continuous' && <ContinuousMetrics metrics={continuousResults} />}
          {activeTab === 'bayesian' && <BayesianInsightsComponent insights={bayesianInsights} />}
        </div>
      </div>
    </>
  );
};

export default Dashboard;