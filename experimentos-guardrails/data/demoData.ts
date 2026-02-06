import type { HealthCheckResult, AnalysisResult, BayesianInsights } from '../api/client';

/**
 * Pre-computed demo data for the interactive tutorial.
 * Based on a hypothetical demo_launch experiment:
 * - control: 10,000 users, 1,000 conversions (10%)
 * - treatment: 10,000 users, 1,200 conversions (12%)
 * - guardrail: error_count (no degradation)
 */

export const DEMO_HEALTH_RESULT: HealthCheckResult = {
  status: 'ok',
  result: {
    overall_status: 'Healthy',
    schema: { status: 'Healthy', issues: [] },
    srm: { status: 'Healthy', message: 'No SRM detected (p=0.999)', p_value: 0.999 },
  },
  preview: [
    { variant: 'control', users: 10000, conversions: 1000, error_count: 50 },
    { variant: 'treatment', users: 10000, conversions: 1200, error_count: 48 },
  ],
  columns: ['variant', 'users', 'conversions', 'error_count'],
  filename: 'demo_launch.csv',
};

export const DEMO_ANALYSIS_RESULT: AnalysisResult = {
  status: 'ok',
  primary_result: {
    control: { users: 10000, conversions: 1000, rate: 0.1 },
    treatment: { users: 10000, conversions: 1200, rate: 0.12 },
    absolute_lift: 0.02,
    relative_lift: 0.2,
    ci_95: [0.011, 0.029],
    p_value: 0.0001,
    is_significant: true,
  },
  guardrail_results: [
    {
      name: 'error_count',
      control_count: 50,
      treatment_count: 48,
      control_rate: 0.005,
      treatment_rate: 0.0048,
      delta: -0.0002,
      relative_lift: -0.04,
      worsened: false,
      severe: false,
      p_value: 0.87,
    },
  ],
};

export const DEMO_BAYESIAN_INSIGHTS: BayesianInsights = {
  conversion: {
    prob_treatment_beats_control: 0.9998,
    expected_loss: 0.000012,
    control_posterior: { alpha: 1001, beta: 9001 },
    treatment_posterior: { alpha: 1201, beta: 8801 },
  },
  continuous: {},
};
