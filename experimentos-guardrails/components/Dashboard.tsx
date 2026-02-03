import React, { useMemo } from 'react';
import StatsCard from './StatsCard';
import MetricsTable from './MetricsTable';
import Icon from './Icon';
import { AnalysisResult, HealthCheckResult } from '../api/client';

interface DashboardProps {
  data: AnalysisResult;
  health: HealthCheckResult | null;
}

const Dashboard: React.FC<DashboardProps> = ({ data, health }) => {
  const primary = data.primary_result;
  const guardrails = data.guardrail_results;

  // Derive stats
  const totalGuardrails = guardrails.length;
  const severeGuardrails = guardrails.filter((g: any) => g.severe).length;
  const worsenedGuardrails = guardrails.filter((g: any) => g.worsened).length;

  const liftPercentage = (primary.relative_lift * 100).toFixed(2);
  const isPositive = primary.relative_lift > 0;
  const pValue = primary.p_value.toFixed(4);
  const isSignificant = primary.is_significant;

  return (
    <>
      <header className="flex flex-col gap-6 p-6 pb-4 shrink-0 z-10">
        <div className="flex flex-wrap items-start justify-between gap-4">

          {/* Title Area */}
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
              <span className="">
                N={primary.control.users + primary.treatment.users}
              </span>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-3">
            {/* 
            <button className="h-10 px-4 rounded-xl border border-white/10 bg-white/5 hover:bg-white/10 hover:border-white/20 text-white text-sm font-medium transition-all flex items-center gap-2 group backdrop-blur-sm">
              <Icon name="download" className="text-white/60 group-hover:text-white transition-colors" size={18} />
              Export
            </button>
             */}
          </div>
        </div>

        {/* Stats Grid */}
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
            subValue={
              <span className="text-primary text-xs font-mono font-medium mb-1">
                95% CI
              </span>
            }
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

      {/* Tabs */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="flex gap-2 px-6 pb-4 border-b border-white/10">
          <button className="px-4 py-2 rounded-lg bg-primary text-white font-medium">
            Primary
          </button>
          <button className="px-4 py-2 rounded-lg bg-white/5 text-white/70 hover:bg-white/10 transition-colors font-medium">
            Guardrails
          </button>
        </div>

        <div className="flex-1 overflow-auto">
          <MetricsTable data={data} />
        </div>
      </div>
    </>
  );
};

export default Dashboard;