import React from 'react';
import {
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  Scatter,
  ComposedChart,
} from 'recharts';
import { CHART_COLORS, DARK_AXIS_PROPS } from './chartTheme';
import { generatePowerCurve, powerForSampleSize } from './chartUtils';

interface PowerCurveProps {
  baselineRate: number;    // e.g. 0.10 for 10%
  mdeRelative: number;     // e.g. 0.10 for 10% relative lift
  alpha?: number;          // significance level, default 0.05
  currentN?: number;       // current sample size per variation (optional marker)
}

const CustomTooltip: React.FC<{
  active?: boolean;
  payload?: Array<{ payload: { n: number; power: number } }>;
}> = ({ active, payload }) => {
  if (!active || !payload?.[0]) return null;
  const d = payload[0].payload;
  return (
    <div className="bg-slate-900/95 border border-white/10 rounded-lg px-3 py-2 text-xs font-mono backdrop-blur-sm">
      <div className="text-white/70">Sample size: <span className="text-white">{d.n.toLocaleString()}</span></div>
      <div className="text-white/70">Power: <span className="text-white">{(d.power * 100).toFixed(1)}%</span></div>
    </div>
  );
};

const PowerCurve: React.FC<PowerCurveProps> = ({
  baselineRate,
  mdeRelative,
  alpha = 0.05,
  currentN,
}) => {
  const curveData = generatePowerCurve(baselineRate, mdeRelative, alpha, currentN);

  // Current point marker data
  const markerData = currentN != null
    ? [{ n: currentN, power: powerForSampleSize(currentN, baselineRate, mdeRelative, alpha) }]
    : [];

  return (
    <div className="bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur-xl">
      <h3 className="text-lg font-semibold text-white mb-1">Power Curve</h3>
      <p className="text-white/50 text-xs mb-4 font-mono">
        Sample size vs statistical power (1-&beta;)
      </p>
      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart
          margin={{ top: 10, right: 20, bottom: 10, left: 10 }}
          data={curveData}
        >
          <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.grid} />
          <XAxis
            dataKey="n"
            type="number"
            tickFormatter={(v: number) => v >= 1000 ? `${(v / 1000).toFixed(0)}k` : String(v)}
            {...DARK_AXIS_PROPS}
            label={{
              value: 'Sample Size (per arm)',
              position: 'insideBottomRight',
              offset: -5,
              fill: CHART_COLORS.axis,
              fontSize: 10,
              fontFamily: 'monospace',
            }}
          />
          <YAxis
            domain={[0, 1]}
            tickFormatter={(v: number) => `${(v * 100).toFixed(0)}%`}
            {...DARK_AXIS_PROPS}
            label={{
              value: 'Power',
              angle: -90,
              position: 'insideLeft',
              offset: 10,
              fill: CHART_COLORS.axis,
              fontSize: 10,
              fontFamily: 'monospace',
            }}
          />
          {/* 80% power threshold line */}
          <ReferenceLine
            y={0.8}
            stroke={CHART_COLORS.powerThreshold}
            strokeDasharray="6 4"
            strokeWidth={1.5}
            label={{
              value: '80%',
              position: 'right',
              fill: CHART_COLORS.powerThreshold,
              fontSize: 10,
              fontFamily: 'monospace',
            }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Line
            type="monotone"
            dataKey="power"
            stroke={CHART_COLORS.primary}
            strokeWidth={2.5}
            dot={false}
            activeDot={{ r: 4, strokeWidth: 2, stroke: 'white' }}
          />
          {markerData.length > 0 && (
            <Scatter
              data={markerData}
              dataKey="power"
              fill={CHART_COLORS.treatment}
              shape={(props: Record<string, unknown>) => {
                const { cx, cy } = props as { cx: number; cy: number };
                return (
                  <g>
                    <circle cx={cx} cy={cy} r={7} fill={CHART_COLORS.treatment} stroke="white" strokeWidth={2} />
                    <text x={cx} y={cy - 14} textAnchor="middle" fill="white" fontSize={10} fontFamily="monospace">
                      Current
                    </text>
                  </g>
                );
              }}
            />
          )}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};

export default PowerCurve;
