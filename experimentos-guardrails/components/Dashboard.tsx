import React, { useState } from 'react';
import StatsCard from './StatsCard';
import MetricsTable from './MetricsTable';
import ForestPlot from './charts/ForestPlot';
import Icon from './Icon';
import {
  AnalysisResult,
  HealthCheckResult,
  ContinuousMetricResult,
  isMultiVariantPrimary,
  isMultiVariantGuardrails,
} from '../api/client';
import type { BayesianInsightsUnion } from '../api/client';
import { ContinuousMetrics } from './ContinuousMetrics';
import { BayesianInsightsComponent } from './BayesianInsights';

interface DashboardProps {
  data: AnalysisResult;
  health: HealthCheckResult | null;
  continuousResults?: ContinuousMetricResult[];
  bayesianInsights?: BayesianInsightsUnion | null;
}

type TabType = 'primary' | 'guardrails' | 'continuous' | 'bayesian';

const Dashboard: React.FC<DashboardProps> = ({ data, health, continuousResults = [], bayesianInsights = null }) => {
  const [activeTab, setActiveTab] = useState<TabType>('primary');
  const primary = data.primary_result;
  const guardrails = data.guardrail_results;
  const isMulti = isMultiVariantPrimary(primary);

  // Derive stats based on variant type
  let liftPercentage: string;
  let isPositive: boolean;
  let pValue: string;
  let isSignificant: boolean;
  let totalUsers: number;
  let totalGuardrails: number;
  let severeGuardrails: number;
  let bestVariantLabel = '';

  if (isMulti) {
    const best = primary.best_variant;
    const bestData = best ? primary.variants[best] : undefined;
    liftPercentage = bestData ? ((bestData.relative_lift ?? 0) * 100).toFixed(2) : '0.00';
    isPositive = bestData ? bestData.absolute_lift > 0 : false;
    pValue = primary.overall.p_value.toFixed(4);
    isSignificant = primary.overall.is_significant;
    totalUsers = primary.control_stats.users + Object.values(primary.variants).reduce((s, v) => s + v.users, 0);
    bestVariantLabel = best ? ` (${best})` : '';

    if (isMultiVariantGuardrails(guardrails)) {
      const allEntries = Object.values(guardrails.by_variant).flat();
      totalGuardrails = new Set(allEntries.map(g => g.name)).size;
      severeGuardrails = guardrails.any_severe ? guardrails.summary.filter(s => s.severe).length : 0;
    } else {
      totalGuardrails = 0;
      severeGuardrails = 0;
    }
  } else {
    liftPercentage = (primary.relative_lift * 100).toFixed(2);
    isPositive = primary.relative_lift > 0;
    pValue = primary.p_value.toFixed(4);
    isSignificant = primary.is_significant;
    totalUsers = primary.control.users + primary.treatment.users;

    const grList = Array.isArray(guardrails) ? guardrails : [];
    totalGuardrails = grList.length;
    severeGuardrails = grList.filter(g => g.severe).length;
  }

  const tabs = [
    { id: 'primary' as TabType, label: 'Primary', icon: '📊' },
    { id: 'guardrails' as TabType, label: 'Guardrails', icon: '🛡️' },
    { id: 'continuous' as TabType, label: 'Continuous', icon: '📈', badge: continuousResults.length },
    { id: 'bayesian' as TabType, label: 'Bayesian', icon: 'ℹ️' },
  ];

  return (
    <div className="flex flex-col h-[calc(100vh-6rem)] overflow-hidden">
      <header className="flex flex-col gap-6 p-4 sm:p-6 pb-4 shrink-0 z-10">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex flex-col gap-1">
            <div className="flex flex-wrap items-center gap-2 sm:gap-3">
              <h2 className="text-white text-2xl sm:text-3xl font-bold tracking-tight font-display drop-shadow-sm">Experiment Results</h2>
              <span className="px-2 py-0.5 rounded-lg text-[10px] font-bold font-mono bg-primary/20 text-primary uppercase border border-primary/20 tracking-wider backdrop-blur-sm shadow-glow-primary">
                Analysis Complete
              </span>
              {isMulti && (
                <span className="px-2 py-0.5 rounded-lg text-[10px] font-bold font-mono bg-purple-500/20 text-purple-400 uppercase border border-purple-500/20 tracking-wider">
                  Multi-Variant ({data.variant_count ?? Object.keys((primary as typeof primary & { variants: Record<string, unknown> }).variants).length + 1})
                </span>
              )}
            </div>
            <div className="flex items-center gap-3 text-white/60 text-sm font-mono mt-1">
              <span className="hover:text-white transition-colors cursor-pointer bg-white/5 px-2 py-0.5 rounded border border-white/5">
                {health?.filename || "data.csv"}
              </span>
              <span className="w-1 h-1 rounded-full bg-white/30"></span>
              <span>N={totalUsers.toLocaleString()}</span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4" data-tour="stats-cards">
          <StatsCard
            title={`Primary Lift${bestVariantLabel}`}
            value={`${isPositive ? '+' : ''}${liftPercentage}%`}
            icon={isPositive ? "trending_up" : "trending_down"}
            subValue={
              <span className={`text-xs font-mono font-medium mb-1 px-1.5 py-0.5 rounded border ${isSignificant ? 'bg-primary/10 text-primary border-primary/10' : 'bg-white/5 text-white/50 border-white/5'}`}>
                {isSignificant ? 'Significant' : 'Not Significant'}
              </span>
            }
          />
          <StatsCard
            title={isMulti ? "Overall P-Value" : "P-Value"}
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

      <div className="flex-1 flex flex-col min-h-0">
        <div className="flex gap-2 px-4 sm:px-6 pb-4 border-b border-white/10 overflow-x-auto shrink-0" data-tour="dashboard-tabs">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`focus-ring px-4 py-2 rounded-lg font-medium transition-all flex items-center gap-2 shrink-0 ${activeTab === tab.id
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

        <div className="flex-1 overflow-y-auto p-4 sm:p-6 pb-16 custom-scrollbar">
          {activeTab === 'primary' && (
            <div className="space-y-6">
              <MetricsTable data={data} />
              {!isMulti && <ForestPlot primary={primary} guardrails={Array.isArray(guardrails) ? guardrails : []} />}
              {isMulti && <ForestPlot primary={primary} guardrails={[]} />}
            </div>
          )}
          {activeTab === 'guardrails' && (
            <div className="space-y-4">
              <h3 className="text-xl font-semibold text-white mb-4">Guardrail Metrics</h3>
              {isMulti && isMultiVariantGuardrails(guardrails) ? (
                <MultiVariantGuardrailView guardrails={guardrails} />
              ) : (
                <>
                  {Array.isArray(guardrails) && guardrails.length === 0 ? (
                    <div className="empty-state">
                      <Icon name="shield" size={48} className="empty-state-icon" />
                      <p className="empty-state-title">No guardrails specified</p>
                      <p className="empty-state-description">Add guardrail columns to your CSV to monitor safety metrics.</p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {Array.isArray(guardrails) && guardrails.map((g, idx) => (
                        <GuardrailCard key={idx} g={g} />
                      ))}
                    </div>
                  )}
                </>
              )}
            </div>
          )}
          {activeTab === 'continuous' && <ContinuousMetrics metrics={continuousResults} />}
          {activeTab === 'bayesian' && <BayesianInsightsComponent insights={bayesianInsights} />}
        </div>
      </div>
    </div>
  );
};

// Guardrail card for 2-variant
interface GuardrailCardProps {
  g: { name: string; control_rate: number; treatment_rate: number; delta: number; severe: boolean; worsened: boolean };
}

const GuardrailCard: React.FC<GuardrailCardProps> = ({ g }) => (
  <div className="glass-card p-6">
    <div className="flex items-center justify-between mb-4">
      <h4 className="text-lg font-semibold text-white">{g.name}</h4>
      <span className={g.severe ? 'status-badge-critical' : g.worsened ? 'status-badge-warning' : 'status-badge-positive'}>
        {g.severe ? 'Severe' : g.worsened ? 'Worsened' : 'OK'}
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
);

// Multi-variant guardrail view
import type { MultiVariantGuardrailResults } from '../api/client';

const VARIANT_COLORS = ['#6366f1', '#34d399', '#f59e0b', '#ec4899', '#06b6d4', '#8b5cf6'];

const MultiVariantGuardrailView: React.FC<{ guardrails: MultiVariantGuardrailResults }> = ({ guardrails }) => {
  const variantNames = Object.keys(guardrails.by_variant);

  return (
    <div className="space-y-6">
      {/* Summary */}
      {guardrails.summary.length > 0 && (
        <div className="glass-card p-4">
          <h4 className="text-sm font-semibold text-white/70 mb-3 uppercase tracking-wider">Summary</h4>
          <div className="space-y-2">
            {guardrails.summary.map((s, i) => (
              <div key={i} className="flex items-center justify-between text-sm">
                <span className="text-white">{s.name}</span>
                <div className="flex items-center gap-3">
                  <span className="text-white/50 font-mono">worst: {s.worst_variant}</span>
                  <span className={s.severe ? 'status-badge-critical' : s.worsened ? 'status-badge-warning' : 'status-badge-positive'}>
                    {s.severe ? 'Severe' : s.worsened ? 'Worsened' : 'OK'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Per-variant tables */}
      {variantNames.map((vName, vi) => {
        const entries = guardrails.by_variant[vName];
        if (!entries) return null;
        const color = VARIANT_COLORS[vi % VARIANT_COLORS.length];
        return (
          <div key={vName} className="glass-card p-4">
            <div className="flex items-center gap-2 mb-3">
              <span className="w-3 h-3 rounded-full" style={{ backgroundColor: color }}></span>
              <h4 className="text-sm font-semibold text-white uppercase tracking-wider">{vName} vs Control</h4>
            </div>
            <div className="overflow-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="text-white/40 text-[11px] font-mono uppercase tracking-widest">
                    <th className="p-2">Metric</th>
                    <th className="p-2 text-right">Control</th>
                    <th className="p-2 text-right">Treatment</th>
                    <th className="p-2 text-right">Delta</th>
                    <th className="p-2 text-right">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {entries.map((g, gi) => (
                    <tr key={gi} className="border-t border-white/5">
                      <td className="p-2 text-white">{g.name}</td>
                      <td className="p-2 text-right text-white/50 font-mono">{(g.control_rate * 100).toFixed(2)}%</td>
                      <td className="p-2 text-right text-white/90 font-mono">{(g.treatment_rate * 100).toFixed(2)}%</td>
                      <td className={`p-2 text-right font-mono ${g.delta > 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {(g.delta * 100).toFixed(3)}pp
                      </td>
                      <td className="p-2 text-right">
                        <span className={g.severe ? 'status-badge-critical' : g.worsened ? 'status-badge-warning' : 'status-badge-positive'}>
                          {g.severe ? 'Severe' : g.worsened ? 'Worsened' : 'OK'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default Dashboard;
