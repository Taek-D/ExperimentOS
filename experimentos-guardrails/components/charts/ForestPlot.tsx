import React from 'react';
import {
  ComposedChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  ErrorBar,
} from 'recharts';
import type { PrimaryResultUnion, GuardrailResult } from '../../api/client';
import { isMultiVariantPrimary } from '../../api/client';
import { CHART_COLORS, VARIANT_COLORS, DARK_AXIS_PROPS } from './chartTheme';

interface ForestPlotProps {
  primary: PrimaryResultUnion;
  guardrails: GuardrailResult[];
}

interface PlotPoint {
  name: string;
  y: number;
  effect: number;
  ciLow: number;
  ciHigh: number;
  errorMinus: number;
  errorPlus: number;
  color: string;
  status: string;
}

function buildPoints(primary: PrimaryResultUnion, guardrails: GuardrailResult[]): PlotPoint[] {
  const points: PlotPoint[] = [];
  let yIndex = 0;

  if (isMultiVariantPrimary(primary)) {
    // Multi-variant: one point per variant
    const variantEntries = Object.entries(primary.variants);
    variantEntries.forEach(([vName, vData], i) => {
      const ciLow = vData.ci_95[0];
      const ciHigh = vData.ci_95[1];
      const effect = vData.absolute_lift;
      const isBest = vName === primary.best_variant;
      const color = VARIANT_COLORS[i % VARIANT_COLORS.length] ?? CHART_COLORS.primary;

      points.push({
        name: `${vName}${isBest ? ' ★' : ''}`,
        y: yIndex,
        effect,
        ciLow,
        ciHigh,
        errorMinus: effect - ciLow,
        errorPlus: ciHigh - effect,
        color: vData.is_significant_corrected ? color : CHART_COLORS.neutral,
        status: vData.is_significant_corrected ? 'Significant (corrected)' : 'Not Significant',
      });
      yIndex += 1;
    });
  } else {
    // 2-variant: original logic
    const ciLow = primary.ci_95[0];
    const ciHigh = primary.ci_95[1];
    const effect = primary.absolute_lift;

    points.push({
      name: 'Primary (Conversion)',
      y: yIndex,
      effect,
      ciLow,
      ciHigh,
      errorMinus: effect - ciLow,
      errorPlus: ciHigh - effect,
      color: primary.is_significant ? CHART_COLORS.primary : CHART_COLORS.neutral,
      status: primary.is_significant ? 'Significant' : 'Not Significant',
    });
    yIndex += 1;
  }

  // Guardrail metrics (2-variant only passes these)
  for (const g of guardrails) {
    const delta = g.delta;
    points.push({
      name: g.name,
      y: yIndex,
      effect: delta,
      ciLow: delta,
      ciHigh: delta,
      errorMinus: 0,
      errorPlus: 0,
      color: g.severe ? CHART_COLORS.danger : g.worsened ? CHART_COLORS.warning : CHART_COLORS.treatment,
      status: g.severe ? 'Severe' : g.worsened ? 'Worsened' : 'OK',
    });
    yIndex += 1;
  }

  return points;
}

const CustomTooltip: React.FC<{
  active?: boolean;
  payload?: Array<{ payload: PlotPoint }>;
}> = ({ active, payload }) => {
  if (!active || !payload?.[0]) return null;
  const d = payload[0].payload;
  return (
    <div className="bg-slate-900/95 border border-white/10 rounded-lg px-3 py-2 text-xs font-mono backdrop-blur-sm">
      <div className="text-white font-semibold mb-1">{d.name}</div>
      <div className="text-white/70">Effect: {(d.effect * 100).toFixed(3)}%</div>
      {d.errorMinus > 0 && (
        <div className="text-white/70">
          95% CI: [{(d.ciLow * 100).toFixed(3)}%, {(d.ciHigh * 100).toFixed(3)}%]
        </div>
      )}
      <div style={{ color: d.color }} className="font-medium mt-1">{d.status}</div>
    </div>
  );
};

const ForestPlot: React.FC<ForestPlotProps> = ({ primary, guardrails }) => {
  const points = buildPoints(primary, guardrails);
  const names = points.map((p) => p.name);

  // Determine x-axis domain from all effects and CIs
  const allValues = points.flatMap((p) => [p.ciLow, p.ciHigh, p.effect]);
  const absMax = Math.max(...allValues.map(Math.abs), 0.001);
  const padding = absMax * 0.3;
  const xMin = -absMax - padding;
  const xMax = absMax + padding;

  return (
    <div className="bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur-xl" data-tour="forest-plot">
      <h3 className="text-lg font-semibold text-white mb-1">Forest Plot</h3>
      <p className="text-white/50 text-xs mb-4 font-mono">
        Effect sizes with 95% confidence intervals
      </p>
      <ResponsiveContainer width="100%" height={Math.max(160, points.length * 56 + 60)}>
        <ComposedChart
          layout="vertical"
          margin={{ top: 10, right: 30, bottom: 10, left: 140 }}
          data={points}
        >
          <CartesianGrid
            horizontal={false}
            strokeDasharray="3 3"
            stroke={CHART_COLORS.grid}
          />
          <XAxis
            type="number"
            domain={[xMin, xMax]}
            tickFormatter={(v: number) => `${(v * 100).toFixed(1)}%`}
            {...DARK_AXIS_PROPS}
          />
          <YAxis
            type="category"
            dataKey="y"
            tickFormatter={(v: number) => names[v] ?? ''}
            width={130}
            {...DARK_AXIS_PROPS}
            tick={{ ...DARK_AXIS_PROPS.tick, textAnchor: 'end' }}
          />
          <ReferenceLine
            x={0}
            stroke={CHART_COLORS.zeroLine}
            strokeDasharray="6 4"
            strokeWidth={1.5}
            label={{
              value: 'No Effect',
              position: 'top',
              fill: CHART_COLORS.zeroLine,
              fontSize: 10,
              fontFamily: 'monospace',
            }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Scatter
            dataKey="effect"
            fill={CHART_COLORS.primary}
            shape={(props: Record<string, unknown>) => {
              const { cx, cy, payload } = props as { cx: number; cy: number; payload: PlotPoint };
              return (
                <circle
                  cx={cx}
                  cy={cy}
                  r={6}
                  fill={payload.color}
                  stroke="white"
                  strokeWidth={1.5}
                />
              );
            }}
          >
            <ErrorBar
              dataKey="errorPlus"
              direction="x"
              stroke={CHART_COLORS.primaryLight}
              strokeWidth={1.5}
            />
          </Scatter>
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};

export default ForestPlot;
