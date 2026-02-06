/** Shared chart color palette and styles for Recharts components */

export const CHART_COLORS = {
  primary: '#6366f1',     // indigo-500 (matches Tailwind primary)
  primaryLight: '#818cf8', // indigo-400
  control: '#60a5fa',     // blue-400
  treatment: '#34d399',   // emerald-400
  danger: '#f87171',      // red-400
  warning: '#fbbf24',     // amber-400
  neutral: '#94a3b8',     // slate-400
  grid: 'rgba(255,255,255,0.08)',
  axis: 'rgba(255,255,255,0.4)',
  zeroLine: '#f87171',
  powerThreshold: '#fbbf24',
} as const;

export const CHART_FONT = {
  family: 'ui-monospace, SFMono-Regular, monospace',
  size: 11,
} as const;

/** Common axis props for dark theme charts */
export const DARK_AXIS_PROPS = {
  stroke: CHART_COLORS.axis,
  tick: { fill: CHART_COLORS.axis, fontSize: CHART_FONT.size, fontFamily: CHART_FONT.family },
  axisLine: { stroke: CHART_COLORS.grid },
  tickLine: { stroke: CHART_COLORS.grid },
} as const;
