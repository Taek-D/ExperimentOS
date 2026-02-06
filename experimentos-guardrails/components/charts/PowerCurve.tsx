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
  baselineRate: number;
  mdeRelative: number;
  alpha?: number;
  currentN?: number;
}

const CustomTooltip: React.FC<{
  active?: boolean;
  payload?: Array<{ payload: { n: number; power: number } }>;
}> = ({ active, payload }) => {
  if (!active || !payload?.[0]) return null;
  const d = payload[0].payload;
  return (
    <div className="bg-surface-1/95 border border-white/10 rounded-lg px-3 py-2 text-xs font-mono backdrop-blur-md">
      <div className="text-white/50">Sample size: <span className="text-white">{d.n.toLocaleString()}</span></div>
      <div className="text-white/50">Power: <span className="text-white">{(d.power * 100).toFixed(1)}%</span></div>
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

  const markerData = currentN != null
    ? [{ n: currentN, power: powerForSampleSize(currentN, baselineRate, mdeRelative, alpha) }]
    : [];

  return (
    <div className="glass-card p-5">
      <h3 className="text-base font-semibold text-white mb-0.5">Power Curve</h3>
      <p className="text-white/30 text-[10px] mb-4 font-mono uppercase tracking-wider">
        Sample size vs statistical power (1-beta)
      </p>
      <div className="overflow-x-auto -mx-2 px-2">
        <div style={{ minWidth: '480px' }}>
      <ResponsiveContainer width="100%" height={280}>
        <ComposedChart
          margin={{ top: 24, right: 20, bottom: 10, left: 10 }}
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
              fontSize: 9,
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
              fontSize: 9,
              fontFamily: 'monospace',
            }}
          />
          <ReferenceLine
            y={0.8}
            stroke={CHART_COLORS.powerThreshold}
            strokeDasharray="6 4"
            strokeWidth={1.5}
            label={{
              value: '80%',
              position: 'right',
              fill: CHART_COLORS.powerThreshold,
              fontSize: 9,
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
                    <circle cx={cx} cy={cy} r={6} fill={CHART_COLORS.treatment} stroke="rgba(255,255,255,0.5)" strokeWidth={1.5} />
                    <text x={cx} y={cy - 12} textAnchor="middle" fill="white" fontSize={9} fontFamily="monospace">
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
      </div>
    </div>
  );
};

export default PowerCurve;
