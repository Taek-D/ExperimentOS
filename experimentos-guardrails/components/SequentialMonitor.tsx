import { useState, useCallback } from 'react';
import type {
  SequentialResult, BoundaryPoint, SequentialProgress, SequentialParams,
  SequentialAnalysisResponse,
} from '../types';
import { runSequentialAnalysis, getSequentialBoundaries } from '../api/client';
import BoundaryChart from './charts/BoundaryChart';
import Icon from './Icon';

export default function SequentialMonitor() {
  // Form state
  const [controlUsers, setControlUsers] = useState(5000);
  const [controlConversions, setControlConversions] = useState(600);
  const [treatmentUsers, setTreatmentUsers] = useState(5100);
  const [treatmentConversions, setTreatmentConversions] = useState(680);
  const [targetSampleSize, setTargetSampleSize] = useState(20000);
  const [currentLook, setCurrentLook] = useState(2);
  const [maxLooks, setMaxLooks] = useState(5);
  const [alpha, setAlpha] = useState(0.05);
  const [boundaryType, setBoundaryType] = useState<'obrien_fleming' | 'pocock'>('obrien_fleming');

  // Result state
  const [result, setResult] = useState<SequentialAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Look history
  const [lookHistory, setLookHistory] = useState<Array<{
    look: number;
    z_stat: number;
    info_fraction: number;
    cumulative_alpha_spent: number;
  }>>([]);

  const handleAnalyze = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: SequentialParams = {
        controlUsers,
        controlConversions,
        treatmentUsers,
        treatmentConversions,
        targetSampleSize,
        currentLook,
        maxLooks,
        alpha,
        boundaryType,
        previousLooks: lookHistory.length > 0 ? lookHistory : undefined,
      };
      const res = await runSequentialAnalysis(params);
      setResult(res);

      // Add to look history
      const seq = res.sequential_result;
      setLookHistory((prev) => {
        const filtered = prev.filter((h) => h.look !== seq.current_look);
        return [
          ...filtered,
          {
            look: seq.current_look,
            z_stat: seq.z_stat,
            info_fraction: seq.info_fraction,
            cumulative_alpha_spent: seq.cumulative_alpha_spent,
          },
        ].sort((a, b) => a.look - b.look);
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setLoading(false);
    }
  }, [controlUsers, controlConversions, treatmentUsers, treatmentConversions,
      targetSampleSize, currentLook, maxLooks, alpha, boundaryType, lookHistory]);

  const handleReset = useCallback(() => {
    setResult(null);
    setLookHistory([]);
    setError(null);
  }, []);

  const seq = result?.sequential_result;
  const progress = result?.progress;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-white flex items-center gap-2">
            <Icon name="monitoring" size={24} />
            Sequential Testing Monitor
          </h2>
          <p className="text-sm text-white/50 mt-1">
            Group Sequential Design for safe early stopping
          </p>
        </div>
        {lookHistory.length > 0 && (
          <button
            onClick={handleReset}
            className="px-3 py-1.5 text-xs rounded-lg bg-white/5 hover:bg-white/10 text-white/60 transition-colors"
          >
            Reset History
          </button>
        )}
      </div>

      {/* Input Form */}
      <div className="bg-white/[0.03] rounded-xl border border-white/[0.06] p-5">
        <h3 className="text-sm font-medium text-white/70 mb-4">Experiment Data</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <InputField label="Control Users" value={controlUsers} onChange={setControlUsers} />
          <InputField label="Control Conversions" value={controlConversions} onChange={setControlConversions} />
          <InputField label="Treatment Users" value={treatmentUsers} onChange={setTreatmentUsers} />
          <InputField label="Treatment Conversions" value={treatmentConversions} onChange={setTreatmentConversions} />
        </div>

        <h3 className="text-sm font-medium text-white/70 mt-5 mb-4">Sequential Settings</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <InputField label="Target Sample Size" value={targetSampleSize} onChange={setTargetSampleSize} />
          <InputField label="Current Look" value={currentLook} onChange={setCurrentLook} />
          <InputField label="Max Looks" value={maxLooks} onChange={setMaxLooks} />
          <div>
            <label className="block text-xs text-white/40 mb-1.5">Boundary Type</label>
            <select
              value={boundaryType}
              onChange={(e) => setBoundaryType(e.target.value as 'obrien_fleming' | 'pocock')}
              className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-sm text-white focus:border-indigo-500 focus:outline-none"
            >
              <option value="obrien_fleming">O&apos;Brien-Fleming</option>
              <option value="pocock">Pocock</option>
            </select>
          </div>
        </div>

        <div className="mt-5 flex items-center gap-3">
          <button
            onClick={handleAnalyze}
            disabled={loading}
            className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-600/50 rounded-lg text-sm font-medium text-white transition-colors flex items-center gap-2"
          >
            {loading ? (
              <>
                <span className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <Icon name="play_arrow" size={18} />
                Run Analysis
              </>
            )}
          </button>
          <span className="text-xs text-white/30">
            Alpha: {alpha}
          </span>
        </div>

        {error && (
          <p className="mt-3 text-sm text-red-400">{error}</p>
        )}
      </div>

      {/* Results */}
      {result && seq && progress && (
        <>
          {/* Progress Bar */}
          <div className="bg-white/[0.03] rounded-xl border border-white/[0.06] p-5">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-white/60">
                Progress: Look {seq.current_look} / {seq.max_looks}
              </span>
              <span className="text-sm font-mono text-white/80">
                {progress.percentage.toFixed(1)}%
              </span>
            </div>
            <div className="w-full h-2 bg-white/5 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{
                  width: `${Math.min(progress.percentage, 100)}%`,
                  backgroundColor: seq.can_stop
                    ? (seq.decision === 'reject_null' ? '#00e5a0' : '#ff4d6a')
                    : '#6366f1',
                }}
              />
            </div>
            <div className="flex items-center justify-between mt-2 text-xs text-white/40">
              <span>{progress.current_sample.toLocaleString()} samples</span>
              <span>Target: {progress.target_sample.toLocaleString()}</span>
            </div>
          </div>

          {/* Decision Card */}
          <DecisionCard sequential={seq} />

          {/* Boundary Chart */}
          <div className="bg-white/[0.03] rounded-xl border border-white/[0.06] p-5">
            <BoundaryChart
              boundaries={result.boundaries}
              currentLook={{
                infoFraction: seq.info_fraction,
                zStat: seq.z_stat,
              }}
              previousLooks={lookHistory
                .filter((h) => h.look !== seq.current_look)
                .map((h) => ({ infoFraction: h.info_fraction, zStat: h.z_stat }))}
            />
          </div>

          {/* Look History Table */}
          <div className="bg-white/[0.03] rounded-xl border border-white/[0.06] p-5">
            <h3 className="text-sm font-medium text-white/70 mb-3">Look History</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-white/40 text-xs border-b border-white/5">
                    <th className="text-left py-2 px-3">Look</th>
                    <th className="text-left py-2 px-3">Info Fraction</th>
                    <th className="text-left py-2 px-3">Z-stat</th>
                    <th className="text-left py-2 px-3">Boundary</th>
                    <th className="text-left py-2 px-3">Result</th>
                  </tr>
                </thead>
                <tbody>
                  {result.boundaries.map((b) => {
                    const histEntry = lookHistory.find((h) => h.look === b.look);
                    const isCurrent = b.look === seq.current_look;
                    return (
                      <tr
                        key={b.look}
                        className={`border-b border-white/5 ${isCurrent ? 'bg-indigo-500/10' : ''}`}
                      >
                        <td className="py-2 px-3 text-white/80 font-mono">
                          {b.look}{isCurrent ? ' *' : ''}
                        </td>
                        <td className="py-2 px-3 text-white/60 font-mono">
                          {b.info_fraction.toFixed(2)}
                        </td>
                        <td className="py-2 px-3 font-mono">
                          {histEntry ? (
                            <span className={Math.abs(histEntry.z_stat) >= b.z_boundary ? 'text-green-400' : 'text-white/60'}>
                              {histEntry.z_stat.toFixed(3)}
                            </span>
                          ) : (
                            <span className="text-white/20">—</span>
                          )}
                        </td>
                        <td className="py-2 px-3 text-red-400/60 font-mono">
                          ±{b.z_boundary.toFixed(3)}
                        </td>
                        <td className="py-2 px-3 text-xs">
                          {histEntry && isCurrent ? (
                            <StatusBadge decision={seq.decision} />
                          ) : histEntry ? (
                            <span className="text-white/40">Continued</span>
                          ) : (
                            <span className="text-white/20">Pending</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Primary Result Summary */}
          <div className="bg-white/[0.03] rounded-xl border border-white/[0.06] p-5">
            <h3 className="text-sm font-medium text-white/70 mb-3">Primary Metric</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <StatBlock label="Control Rate" value={`${(result.primary_result.control_rate * 100).toFixed(2)}%`} />
              <StatBlock label="Treatment Rate" value={`${(result.primary_result.treatment_rate * 100).toFixed(2)}%`} />
              <StatBlock
                label="Absolute Lift"
                value={`${(result.primary_result.absolute_lift * 100).toFixed(2)}%p`}
                highlight={result.primary_result.absolute_lift > 0}
              />
              <StatBlock label="P-value" value={result.primary_result.p_value.toFixed(4)} />
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function InputField({ label, value, onChange }: { label: string; value: number; onChange: (v: number) => void }) {
  return (
    <div>
      <label className="block text-xs text-white/40 mb-1.5">{label}</label>
      <input
        type="number"
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-sm text-white font-mono focus:border-indigo-500 focus:outline-none"
      />
    </div>
  );
}

function DecisionCard({ sequential }: { sequential: SequentialResult }) {
  const defaultStyle = { bg: 'bg-indigo-500/10 border-indigo-500/20', icon: 'hourglass_top', title: 'Continue Collecting Data' };
  const decisionConfig: Record<string, { bg: string; icon: string; title: string }> = {
    reject_null: { bg: 'bg-green-500/10 border-green-500/20', icon: 'check_circle', title: 'Early Stopping Justified' },
    continue: defaultStyle,
    fail_to_reject: { bg: 'bg-amber-500/10 border-amber-500/20', icon: 'do_not_disturb', title: 'No Significant Difference' },
  };
  const c = decisionConfig[sequential.decision] ?? defaultStyle;

  return (
    <div className={`rounded-xl border p-5 ${c.bg}`}>
      <div className="flex items-center gap-3 mb-2">
        <Icon name={c.icon} size={24} />
        <h3 className="text-lg font-semibold text-white">{c.title}</h3>
      </div>
      <p className="text-sm text-white/60">{sequential.message}</p>
      <div className="mt-3 flex flex-wrap gap-4 text-xs text-white/40">
        <span>|z| = {Math.abs(sequential.z_stat).toFixed(3)}</span>
        <span>Boundary = {sequential.z_boundary.toFixed(3)}</span>
        <span>Alpha spent = {sequential.cumulative_alpha_spent.toFixed(4)}</span>
      </div>
    </div>
  );
}

function StatusBadge({ decision }: { decision: string }) {
  if (decision === 'reject_null') return <span className="text-green-400 font-medium">Reject H0</span>;
  if (decision === 'fail_to_reject') return <span className="text-amber-400 font-medium">Fail to Reject</span>;
  return <span className="text-indigo-400 font-medium">Continue</span>;
}

function StatBlock({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div>
      <span className="text-xs text-white/40 block">{label}</span>
      <span className={`text-lg font-mono ${highlight ? 'text-green-400' : 'text-white/80'}`}>
        {value}
      </span>
    </div>
  );
}
