import React, { useMemo } from 'react';
import GlossaryTerm from './GlossaryTerm';
import { AnalysisResult, isMultiVariantPrimary, isMultiVariantGuardrails } from '../api/client';

interface MetricsTableProps {
  data?: AnalysisResult;
}

const MetricsTable: React.FC<MetricsTableProps> = ({ data }) => {
  const isMulti = data ? isMultiVariantPrimary(data.primary_result) : false;

  const rows = useMemo(() => {
    if (!data) return [];

    const p = data.primary_result;
    const g = data.guardrail_results;
    const items: MetricRowData[] = [];

    if (isMultiVariantPrimary(p)) {
      // Multi-variant: Overall summary row
      items.push({
        id: "overall",
        type: "Overall Test",
        name: "Chi-Square (Overall)",
        key: "overall_chi2",
        baseline: "-",
        variant: "-",
        delta: "-",
        pValue: p.overall.p_value.toFixed(4),
        pCorrected: undefined,
        power: "-",
        status: p.overall.is_significant ? "POSITIVE" : "NEUTRAL",
        isCritical: false,
        isWarning: false,
        variantName: undefined,
      });

      // Per-variant rows vs control
      for (const [vName, vData] of Object.entries(p.variants)) {
        const isBest = vName === p.best_variant;
        items.push({
          id: `mv-${vName}`,
          type: isBest ? "Best Variant" : "Variant",
          name: `Conversion Rate (${vName})`,
          key: `primary_${vName}`,
          baseline: (p.control_stats.rate * 100).toFixed(2) + "%",
          variant: (vData.rate * 100).toFixed(2) + "%",
          delta: ((vData.relative_lift != null && vData.relative_lift > 999 ? 999 : (vData.relative_lift ?? 0)) * 100).toFixed(2) + "%",
          pValue: vData.p_value.toFixed(4),
          pCorrected: vData.p_value_corrected.toFixed(4),
          power: "-",
          status: vData.is_significant_corrected ? (vData.absolute_lift > 0 ? "POSITIVE" : "NEGATIVE") : "NEUTRAL",
          isCritical: false,
          isWarning: false,
          variantName: vName,
        });
      }

      // Guardrail rows (multi-variant)
      if (isMultiVariantGuardrails(g)) {
        for (const [vName, entries] of Object.entries(g.by_variant)) {
          if (!entries) continue;
          for (const gr of entries) {
            items.push({
              id: `gr-${vName}-${gr.name}`,
              type: "Guardrail",
              name: `${gr.name} (${vName})`,
              key: `guardrail_${gr.name}_${vName}`,
              baseline: (gr.control_rate * 100).toFixed(2) + "%",
              variant: (gr.treatment_rate * 100).toFixed(2) + "%",
              delta: (gr.delta * 100).toFixed(3) + "pp",
              pValue: gr.p_value > 0 ? gr.p_value.toFixed(4) : "-",
              pCorrected: undefined,
              power: "-",
              status: gr.severe ? "CRITICAL" : (gr.worsened ? "WARNING" : "STABLE"),
              isCritical: gr.severe,
              isWarning: gr.worsened && !gr.severe,
              variantName: vName,
            });
          }
        }
      }
    } else {
      // 2-variant: existing logic
      items.push({
        id: "primary",
        type: "Primary Metric",
        name: "Conversion Rate",
        key: "primary_conversion",
        baseline: (p.control.rate * 100).toFixed(2) + "%",
        variant: (p.treatment.rate * 100).toFixed(2) + "%",
        delta: ((p.relative_lift > 999 ? 999 : p.relative_lift) * 100).toFixed(2) + "%",
        pValue: p.p_value.toFixed(4),
        pCorrected: undefined,
        power: "-",
        status: p.is_significant ? (p.relative_lift > 0 ? "POSITIVE" : "NEGATIVE") : "NEUTRAL",
        isCritical: false,
        isWarning: false,
        variantName: undefined,
      });

      if (Array.isArray(g)) {
        g.forEach((gr, idx) => {
          items.push({
            id: `gr-${idx}`,
            type: "Guardrail",
            name: gr.name,
            key: `guardrail_${gr.name}`,
            baseline: (gr.control_rate * 100).toFixed(2) + "%",
            variant: (gr.treatment_rate * 100).toFixed(2) + "%",
            delta: (gr.delta * 100).toFixed(3) + "pp",
            pValue: gr.p_value > 0 ? gr.p_value.toFixed(4) : "-",
            pCorrected: undefined,
            power: "-",
            status: gr.severe ? "CRITICAL" : (gr.worsened ? "WARNING" : "STABLE"),
            isCritical: gr.severe,
            isWarning: gr.worsened && !gr.severe,
            variantName: undefined,
          });
        });
      }
    }

    return items;
  }, [data]);

  if (!data) return null;

  return (
    <div className="flex-1 flex flex-col min-h-0 px-2 sm:px-6 pb-6" data-tour="metrics-table">
      <div className="flex-1 overflow-auto rounded-2xl border border-white/5 bg-background-dark/30 backdrop-blur-sm shadow-inner relative scroll-smooth custom-scrollbar">
        <table className="w-full text-left border-collapse" style={{ minWidth: '640px' }}>
          <thead className="sticky top-0 z-10 bg-[#15232d]/95 backdrop-blur-md shadow-sm">
            <tr>
              <th className="p-4 pl-6 text-white/40 text-[11px] font-mono uppercase tracking-widest font-semibold border-b border-white/5 w-[30%]">Metric Name</th>
              <th className="p-4 text-white/40 text-[11px] font-mono uppercase tracking-widest font-semibold border-b border-white/5 text-right">Baseline (A)</th>
              <th className="p-4 text-white/40 text-[11px] font-mono uppercase tracking-widest font-semibold border-b border-white/5 text-right">Variant (B)</th>
              <th className="p-4 text-white/40 text-[11px] font-mono uppercase tracking-widest font-semibold border-b border-white/5 text-right"><GlossaryTerm termKey="delta">Delta</GlossaryTerm></th>
              <th className="p-4 text-white/40 text-[11px] font-mono uppercase tracking-widest font-semibold border-b border-white/5 text-right"><GlossaryTerm termKey="p-value">P-Value</GlossaryTerm></th>
              {isMulti && (
                <th className="p-4 text-white/40 text-[11px] font-mono uppercase tracking-widest font-semibold border-b border-white/5 text-right">P (Corrected)</th>
              )}
              <th className="p-4 pr-6 text-white/40 text-[11px] font-mono uppercase tracking-widest font-semibold border-b border-white/5 text-right">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {rows.map((row) => (
              <MetricRow key={row.id} row={row} showCorrected={isMulti} />
            ))}
          </tbody>
        </table>
        <div className="h-8"></div>
      </div>
    </div>
  );
};

interface MetricRowData {
  id: string;
  type: string;
  name: string;
  key: string;
  baseline: string;
  variant: string;
  delta: string;
  pValue: string;
  pCorrected: string | undefined;
  power: string;
  status: string;
  isCritical: boolean;
  isWarning: boolean;
  variantName: string | undefined;
}

interface MetricRowProps {
  row: MetricRowData;
  showCorrected: boolean;
}

const MetricRow: React.FC<MetricRowProps> = ({ row, showCorrected }) => {
  const { isCritical, isWarning } = row;

  let deltaColorClass = 'text-primary';
  if (isCritical) deltaColorClass = 'text-danger bg-danger/10 px-1.5 py-0.5 rounded -mr-1.5';
  if (isWarning) deltaColorClass = 'text-warning';
  if (row.id === 'primary' && row.status === 'NEGATIVE') deltaColorClass = 'text-white/60';

  const isBest = row.type === 'Best Variant';
  const isOverall = row.type === 'Overall Test';

  return (
    <tr className={`group relative transition-all duration-200 ${isCritical ? 'hover:bg-danger/[0.03]' : 'hover:bg-white/[0.02]'}`}>
      <td className="p-4 pl-6 relative">
        {isCritical && (
          <>
            <div className="absolute left-0 top-0 bottom-0 w-0.5 bg-danger shadow-[0_0_12px_rgba(239,68,68,0.8)]"></div>
            <div className="absolute inset-0 bg-gradient-to-r from-danger/5 to-transparent pointer-events-none mix-blend-overlay"></div>
          </>
        )}
        <div className="flex flex-col relative z-10">
          <div className="flex items-center gap-2">
            <span className={`font-medium text-sm transition-colors ${isCritical ? 'text-danger' : 'text-white'}`}>{row.name}</span>
            {row.type === 'Primary Metric' && <span className="text-[10px] bg-primary/20 text-primary px-1.5 rounded">Primary</span>}
            {isBest && <span className="text-[10px] bg-yellow-500/20 text-yellow-400 px-1.5 rounded">Best</span>}
            {isOverall && <span className="text-[10px] bg-blue-500/20 text-blue-400 px-1.5 rounded">Overall</span>}
            {row.type === 'Variant' && <span className="text-[10px] bg-white/10 text-white/50 px-1.5 rounded">Variant</span>}
          </div>
          <span className="text-white/30 text-xs font-mono mt-0.5 group-hover:text-white/50 transition-colors">{row.key}</span>
        </div>
      </td>
      <td className="p-4 text-right font-mono text-sm text-white/50">{row.baseline}</td>
      <td className="p-4 text-right font-mono text-sm text-white/90 font-bold">{row.variant}</td>
      <td className="p-4 text-right font-mono text-sm font-bold">
        <span className={deltaColorClass}>{row.delta}</span>
      </td>
      <td className="p-4 text-right font-mono text-sm text-white/50">{row.pValue}</td>
      {showCorrected && (
        <td className="p-4 text-right font-mono text-sm text-white/50">{row.pCorrected ?? '-'}</td>
      )}
      <td className="p-4 pr-6 text-right">
        <StatusBadge status={row.status} />
      </td>
    </tr>
  );
};

const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  if (status === 'NEGATIVE') return <span className="text-white/50 text-[10px]">No Lift</span>;
  if (status === 'CRITICAL') {
    return (
      <span className="status-badge-critical">
        <span className="w-1.5 h-1.5 rounded-full bg-danger animate-pulse"></span>
        Critical
      </span>
    );
  }
  if (status === 'WARNING') return <span className="status-badge-warning">Warning</span>;
  if (status === 'POSITIVE') return <span className="status-badge-positive">Significant</span>;
  return <span className="status-badge-neutral">Stable</span>;
};

export default MetricsTable;
