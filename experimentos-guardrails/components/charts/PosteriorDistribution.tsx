import React, { useMemo } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from 'recharts';
import { CHART_COLORS, DARK_AXIS_PROPS } from './chartTheme';
import { generateBetaCurve } from './chartUtils';

interface PosteriorParams {
  alpha: number;
  beta: number;
}

interface PosteriorDistributionProps {
  control: PosteriorParams;
  treatment: PosteriorParams;
}

interface CurvePoint {
  x: number;
  control: number;
  treatment: number;
}

const CustomTooltip: React.FC<{
  active?: boolean;
  payload?: Array<{ dataKey: string; value: number; color: string }>;
  label?: number;
}> = ({ active, payload, label }) => {
  if (!active || !payload || label == null) return null;
  return (
    <div className="bg-slate-900/95 border border-white/10 rounded-lg px-3 py-2 text-xs font-mono backdrop-blur-sm">
      <div className="text-white/70 mb-1">Rate: {(label * 100).toFixed(2)}%</div>
      {payload.map((entry) => (
        <div key={entry.dataKey} style={{ color: entry.color }}>
          {entry.dataKey === 'control' ? 'Control' : 'Treatment'}: {entry.value.toFixed(2)}
        </div>
      ))}
    </div>
  );
};

const PosteriorDistribution: React.FC<PosteriorDistributionProps> = ({
  control,
  treatment,
}) => {
  const data = useMemo<CurvePoint[]>(() => {
    const controlCurve = generateBetaCurve(control.alpha, control.beta);
    const treatmentCurve = generateBetaCurve(treatment.alpha, treatment.beta);

    // Merge onto a common x-axis (union of both x values)
    const xSet = new Set<number>();
    for (const p of controlCurve) xSet.add(p.x);
    for (const p of treatmentCurve) xSet.add(p.x);
    const xs = Array.from(xSet).sort((a, b) => a - b);

    // Build lookup maps
    const cMap = new Map(controlCurve.map((p) => [p.x, p.y]));
    const tMap = new Map(treatmentCurve.map((p) => [p.x, p.y]));

    return xs.map((x) => ({
      x,
      control: cMap.get(x) ?? 0,
      treatment: tMap.get(x) ?? 0,
    }));
  }, [control.alpha, control.beta, treatment.alpha, treatment.beta]);

  return (
    <div className="bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur-xl">
      <h3 className="text-lg font-semibold text-white mb-1">Posterior Distribution</h3>
      <p className="text-white/50 text-xs mb-4 font-mono">
        Beta posteriors: Control (blue) vs Treatment (green)
      </p>
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart
          data={data}
          margin={{ top: 10, right: 20, bottom: 10, left: 10 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.grid} />
          <XAxis
            dataKey="x"
            type="number"
            domain={['dataMin', 'dataMax']}
            tickFormatter={(v: number) => `${(v * 100).toFixed(1)}%`}
            {...DARK_AXIS_PROPS}
            label={{
              value: 'Conversion Rate',
              position: 'insideBottomRight',
              offset: -5,
              fill: CHART_COLORS.axis,
              fontSize: 10,
              fontFamily: 'monospace',
            }}
          />
          <YAxis
            {...DARK_AXIS_PROPS}
            label={{
              value: 'Density',
              angle: -90,
              position: 'insideLeft',
              offset: 10,
              fill: CHART_COLORS.axis,
              fontSize: 10,
              fontFamily: 'monospace',
            }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ color: CHART_COLORS.axis, fontSize: 11, fontFamily: 'monospace' }}
          />
          <Area
            type="monotone"
            dataKey="control"
            name="Control"
            stroke={CHART_COLORS.control}
            fill={CHART_COLORS.control}
            fillOpacity={0.25}
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
          />
          <Area
            type="monotone"
            dataKey="treatment"
            name="Treatment"
            stroke={CHART_COLORS.treatment}
            fill={CHART_COLORS.treatment}
            fillOpacity={0.25}
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

export default PosteriorDistribution;
