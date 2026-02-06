/** Shared chart color palette and styles for Recharts components */

export const CHART_COLORS = {
  primary: '#6366f1',     // indigo-500
  primaryLight: '#818cf8', // indigo-400
  control: '#60a5fa',     // blue-400
  treatment: '#00e5a0',   // primary green
  danger: '#ff4d6a',      // red
  warning: '#ffb020',     // amber
  neutral: '#64748b',     // slate-500
  grid: 'rgba(255,255,255,0.05)',
  axis: 'rgba(255,255,255,0.3)',
  zeroLine: '#ff4d6a',
  powerThreshold: '#ffb020',
} as const;

/** Extended palette for multi-variant charts */
export const VARIANT_COLORS = [
  '#6366f1', // indigo-500
  '#00e5a0', // primary green
  '#f59e0b', // amber-500
  '#ec4899', // pink-500
  '#06b6d4', // cyan-500
  '#8b5cf6', // violet-500
  '#f97316', // orange-500
  '#14b8a6', // teal-500
] as const;

export const CHART_FONT = {
  family: 'ui-monospace, SFMono-Regular, monospace',
  size: 10,
} as const;

/** Common axis props for dark theme charts */
export const DARK_AXIS_PROPS = {
  stroke: CHART_COLORS.axis,
  tick: { fill: CHART_COLORS.axis, fontSize: CHART_FONT.size, fontFamily: CHART_FONT.family },
  axisLine: { stroke: CHART_COLORS.grid },
  tickLine: { stroke: CHART_COLORS.grid },
} as const;
