import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceDot, Legend, Area, ComposedChart,
} from 'recharts';
import type { BoundaryPoint } from '../../types';
import { CHART_COLORS, DARK_AXIS_PROPS, CHART_FONT } from './chartTheme';

interface BoundaryChartProps {
  boundaries: BoundaryPoint[];
  currentLook: {
    infoFraction: number;
    zStat: number;
  } | null;
  previousLooks: Array<{
    infoFraction: number;
    zStat: number;
  }>;
}

export default function BoundaryChart({ boundaries, currentLook, previousLooks }: BoundaryChartProps) {
  // Build chart data from boundaries
  const chartData = boundaries.map((b) => ({
    info_fraction: b.info_fraction,
    z_boundary: b.z_boundary,
    neg_z_boundary: -b.z_boundary,
    look: b.look,
  }));

  // Find max z for y-axis range
  const maxZ = Math.max(
    ...boundaries.map((b) => b.z_boundary),
    ...(currentLook ? [Math.abs(currentLook.zStat)] : []),
    ...previousLooks.map((l) => Math.abs(l.zStat)),
    3,
  );
  const yMax = Math.ceil(maxZ + 0.5);

  return (
    <div className="w-full">
      <h4 className="text-xs font-medium text-white/60 mb-2 uppercase tracking-wider">
        Sequential Boundary Chart
      </h4>
      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart data={chartData} margin={{ top: 10, right: 20, bottom: 10, left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.grid} />
          <XAxis
            dataKey="info_fraction"
            {...DARK_AXIS_PROPS}
            label={{
              value: 'Information Fraction',
              position: 'insideBottom',
              offset: -5,
              fill: CHART_COLORS.axis,
              fontSize: CHART_FONT.size,
            }}
            tickFormatter={(v: number) => v.toFixed(1)}
          />
          <YAxis
            domain={[-yMax, yMax]}
            {...DARK_AXIS_PROPS}
            label={{
              value: 'Z-statistic',
              angle: -90,
              position: 'insideLeft',
              fill: CHART_COLORS.axis,
              fontSize: CHART_FONT.size,
            }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1e293b',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: 8,
              fontSize: 11,
              fontFamily: CHART_FONT.family,
            }}
            labelFormatter={(v) => `Info Fraction: ${Number(v).toFixed(2)}`}
            formatter={(value, name) => {
              const label = name === 'z_boundary' ? 'Upper Boundary'
                : name === 'neg_z_boundary' ? 'Lower Boundary'
                : String(name);
              return [Number(value).toFixed(3), label];
            }}
          />
          <Legend
            verticalAlign="top"
            wrapperStyle={{ fontSize: 10, fontFamily: CHART_FONT.family }}
          />

          {/* Rejection boundary (upper) */}
          <Line
            type="monotone"
            dataKey="z_boundary"
            stroke={CHART_COLORS.danger}
            strokeWidth={2}
            dot={false}
            name="Rejection Boundary"
          />

          {/* Rejection boundary (lower, mirrored) */}
          <Line
            type="monotone"
            dataKey="neg_z_boundary"
            stroke={CHART_COLORS.danger}
            strokeWidth={2}
            strokeDasharray="4 4"
            dot={false}
            name="Lower Boundary"
          />

          {/* Zero line */}
          <Line
            type="monotone"
            dataKey={() => 0}
            stroke="rgba(255,255,255,0.15)"
            strokeWidth={1}
            dot={false}
            name=""
            legendType="none"
          />

          {/* Previous looks */}
          {previousLooks.map((look, i) => (
            <ReferenceDot
              key={`prev-${i}`}
              x={look.infoFraction}
              y={look.zStat}
              r={4}
              fill={CHART_COLORS.neutral}
              stroke="white"
              strokeWidth={1}
            />
          ))}

          {/* Current look */}
          {currentLook && (
            <ReferenceDot
              x={currentLook.infoFraction}
              y={currentLook.zStat}
              r={6}
              fill={CHART_COLORS.primary}
              stroke="white"
              strokeWidth={2}
            />
          )}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
